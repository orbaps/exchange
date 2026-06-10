import time
import base64
import hashlib
from typing import Dict, Any, Tuple
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519, padding
from cryptography.hazmat.primitives import hashes, serialization

class FederationKeyPair:
    """Manages asymmetric key pairs for signing and verification."""
    
    @staticmethod
    def generate_rsa() -> Tuple[str, str]:
        """Generates RSA-2048 private and public key in PEM format."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")
        
        return private_pem, public_pem

    @staticmethod
    def generate_ed25519() -> Tuple[str, str]:
        """Generates Ed25519 private and public key in PEM format."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")
        
        return private_pem, public_pem


class FederationVerifier:
    """Signs outbound messages and validates incoming message signatures."""
    
    @staticmethod
    def compute_payload_hash(payload: Dict[str, Any]) -> str:
        """Returns deterministic SHA256 of payload."""
        import json
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    @staticmethod
    def sign_message(
        node_id: str,
        private_key_pem: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Signs payload and returns the signed envelope."""
        timestamp = int(time.time() * 1000)
        payload_hash = FederationVerifier.compute_payload_hash(payload)
        
        # Message content to sign: "node_id:timestamp:payload_hash"
        msg = f"{node_id}:{timestamp}:{payload_hash}".encode("utf-8")
        
        # Load private key
        priv_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"),
            password=None
        )
        
        # Sign depending on key type
        if isinstance(priv_key, ed25519.Ed25519PrivateKey):
            signature_bytes = priv_key.sign(msg)
            algo = "ED25519"
        else:
            # RSA
            signature_bytes = priv_key.sign(
                msg,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            algo = "RSA"
            
        signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")
        
        return {
            "node_id": node_id,
            "timestamp": timestamp,
            "payload_hash": payload_hash,
            "signature": signature_b64,
            "algo": algo,
            "payload": payload
        }

    @staticmethod
    def verify_message(envelope: Dict[str, Any], public_key_pem: str) -> bool:
        """Verifies an incoming signed envelope using the public key."""
        try:
            node_id = envelope["node_id"]
            timestamp = envelope["timestamp"]
            payload_hash = envelope["payload_hash"]
            signature_b64 = envelope["signature"]
            algo = envelope.get("algo", "ED25519")
            payload = envelope["payload"]
            
            # Check payload integrity
            if FederationVerifier.compute_payload_hash(payload) != payload_hash:
                return False
                
            # Reconstruct signed message
            msg = f"{node_id}:{timestamp}:{payload_hash}".encode("utf-8")
            
            # Load public key
            pub_key = serialization.load_pem_public_key(
                public_key_pem.encode("utf-8")
            )
            
            signature_bytes = base64.b64decode(signature_b64)
            
            if isinstance(pub_key, ed25519.Ed25519PublicKey) or algo.upper() == "ED25519":
                pub_key.verify(signature_bytes, msg)
            else:
                # RSA
                pub_key.verify(
                    signature_bytes,
                    msg,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            return True
        except Exception:
            return False
