import base64
import datetime as dt
import hashlib
import io
import json
import zipfile

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from wallet import apple_pass_json, build_pkpass, google_pass, google_save_url


def _cert(cn, key, issuer_key=None, issuer_name=None):
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = dt.datetime.now(dt.timezone.utc)
    return (x509.CertificateBuilder().subject_name(name).issuer_name(issuer_name or name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - dt.timedelta(days=1)).not_valid_after(now + dt.timedelta(days=30))
            .sign(issuer_key or key, hashes.SHA256()))


@pytest.fixture(scope="module")
def apple_creds():
    wwdr_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    wwdr = _cert("Test WWDR", wwdr_key)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert = _cert("Pass Type ID: pass.test.card", key, wwdr_key, wwdr.subject)
    p12 = pkcs12.serialize_key_and_certificates(b"t", key, cert, None,
                                                serialization.BestAvailableEncryption(b"secret"))
    return p12, wwdr.public_bytes(serialization.Encoding.PEM)


def test_apple_pass_json(profile, brand):
    pj = apple_pass_json(profile, brand, "pass.test.card", "ABCDE12345", "KI AffAIrs", valid_days=3,
                         today=dt.date(2026, 11, 20))
    assert pj["formatVersion"] == 1 and pj["passTypeIdentifier"] == "pass.test.card"
    assert pj["barcodes"][0]["message"] == "https://www.linkedin.com/in/mara-beispiel/"
    assert pj["barcodes"][0]["format"] == "PKBarcodeFormatQR"
    assert pj["expirationDate"].startswith("2026-11-22T23:59:59")  # 3 Tage inkl. heute
    assert pj["generic"]["primaryFields"][0]["value"] == "Mara Beispiel"
    assert pj["backgroundColor"].startswith("rgb(")


def test_build_pkpass_is_valid_bundle(profile, brand, apple_creds):
    p12, wwdr = apple_creds
    pj = apple_pass_json(profile, brand, "pass.test.card", "ABCDE12345", "KI AffAIrs")
    data = build_pkpass(pj, {}, p12, b"secret", wwdr)
    z = zipfile.ZipFile(io.BytesIO(data))
    names = set(z.namelist())
    assert {"pass.json", "manifest.json", "signature", "icon.png", "icon@2x.png", "logo.png"} <= names
    manifest = json.loads(z.read("manifest.json"))
    for name, digest in manifest.items():
        assert hashlib.sha1(z.read(name)).hexdigest() == digest
    # Signatur: PKCS#7 (DER), detached, über manifest.json
    from cryptography.hazmat.primitives.serialization import pkcs7
    certs = pkcs7.load_der_pkcs7_certificates(z.read("signature"))
    assert any("Pass Type ID" in c.subject.rfc4514_string() for c in certs)
    assert any("Test WWDR" in c.subject.rfc4514_string() for c in certs)


def test_build_pkpass_wrong_password(profile, brand, apple_creds):
    p12, wwdr = apple_creds
    with pytest.raises(ValueError):
        build_pkpass(apple_pass_json(profile, brand, "pass.t", "T", "X"), {}, p12, b"falsch", wwdr)


def test_google_pass_and_signed_link(profile, brand):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.NoEncryption())
    cls, obj = google_pass(profile, brand, issuer_id="3388000000012345678", valid_days=2,
                           today=dt.date(2026, 11, 20))
    assert obj["classId"] == cls["id"] and obj["id"].startswith("3388000000012345678.")
    assert obj["barcode"]["value"] == "https://www.linkedin.com/in/mara-beispiel/"
    assert obj["validTimeInterval"]["end"]["date"].startswith("2026-11-21T23:59:59")
    assert obj["hexBackgroundColor"].startswith("#")
    url = google_save_url("sa@test.iam.gserviceaccount.com", pem, cls, obj)
    assert url.startswith("https://pay.google.com/gp/v/save/")
    token = url.rsplit("/", 1)[1]
    h, p, s = token.split(".")
    pad = lambda x: x + "=" * (-len(x) % 4)  # noqa: E731
    payload = json.loads(base64.urlsafe_b64decode(pad(p)))
    assert payload["aud"] == "google" and payload["typ"] == "savetowallet"
    assert payload["payload"]["genericObjects"][0]["id"] == obj["id"]
    key.public_key().verify(base64.urlsafe_b64decode(pad(s)), f"{h}.{p}".encode(), padding.PKCS1v15(), hashes.SHA256())


def test_pkpass_signature_verifies_with_openssl(tmp_path, profile, brand, apple_creds):
    import shutil
    import subprocess
    if not shutil.which("openssl"):
        pytest.skip("openssl fehlt")
    p12, wwdr = apple_creds
    z = zipfile.ZipFile(io.BytesIO(build_pkpass(apple_pass_json(profile, brand, "pass.t", "T", "X"), {}, p12,
                                                b"secret", wwdr)))
    (tmp_path / "manifest.json").write_bytes(z.read("manifest.json"))
    (tmp_path / "signature").write_bytes(z.read("signature"))
    (tmp_path / "ca.pem").write_bytes(wwdr)
    r = subprocess.run(["openssl", "smime", "-verify", "-binary", "-inform", "DER", "-in", str(tmp_path / "signature"),
                        "-content", str(tmp_path / "manifest.json"), "-noverify", "-out", "/dev/null"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    # Manipulation fällt auf
    (tmp_path / "manifest.json").write_bytes(z.read("manifest.json").replace(b"{", b"{ ", 1))
    r = subprocess.run(["openssl", "smime", "-verify", "-binary", "-inform", "DER", "-in", str(tmp_path / "signature"),
                        "-content", str(tmp_path / "manifest.json"), "-noverify", "-out", "/dev/null"],
                       capture_output=True, text=True)
    assert r.returncode != 0
