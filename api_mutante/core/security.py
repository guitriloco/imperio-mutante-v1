import hashlib
import json
import secrets
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader

from api_mutante.rag_engine import DATA_DIR

KEYS_DB_FILE = DATA_DIR / "api_keys.json"

# Definição estrita de tiers e limites por minuto/dia
TIER_LIMITS = {
    "FREE": {
        "rpm": 5,          # Requests per minute
        "daily_tokens": 10000,
        "allowed_models": ["gemini-2.5-flash"]
    },
    "PRO": {
        "rpm": 60,
        "daily_tokens": 200000,
        "allowed_models": ["gemini-2.5-flash", "gemini-2.0-flash"]
    },
    "ENTERPRISE": {
        "rpm": 300,
        "daily_tokens": 1000000,
        "allowed_models": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-embedding-001"]
    }
}

class APIKeyManager:
    """Gerenciador criptográfico e validador de cotas de chaves de API com persistência local."""

    def __init__(self):
        self._keys: Dict[str, Dict[str, Any]] = {}
        # Sliding-window rate limiter in-memory: key_hash -> list of timestamps
        self._request_timestamps: Dict[str, list] = defaultdict(list)
        self._load_keys()

    def _hash_key(self, api_key: str) -> str:
        """Gera SHA-256 da chave para armazenamento seguro."""
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    def _load_keys(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if KEYS_DB_FILE.exists():
            try:
                with open(KEYS_DB_FILE, "r", encoding="utf-8") as f:
                    self._keys = json.load(f)
            except Exception:
                self._keys = {}

    def _save_keys(self):
        with open(KEYS_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(self._keys, f, indent=2, ensure_ascii=False)

    def generate_key(self, owner_name: str, tier: str = "FREE") -> Tuple[str, Dict[str, Any]]:
        """Gera uma chave única com prefixo identificável 'mutante_' e salva hash criptográfico."""
        tier_upper = tier.upper()
        if tier_upper not in TIER_LIMITS:
            raise ValueError(f"Tier inválido: {tier}. Disponíveis: {list(TIER_LIMITS.keys())}")

        raw_secret = secrets.token_urlsafe(32)
        api_key = f"mutante_{tier_upper.lower()}_{raw_secret}"
        key_hash = self._hash_key(api_key)

        key_data = {
            "owner": owner_name,
            "tier": tier_upper,
            "created_at": datetime.now().isoformat(),
            "total_requests": 0,
            "is_active": True
        }

        self._keys[key_hash] = key_data
        self._save_keys()
        return api_key, key_data

    def validate_and_rate_limit(self, raw_key: str) -> Dict[str, Any]:
        """Valida autenticidade, status ativo e aplica sliding-window rate limiting em segundos."""
        if not raw_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cabeçalho 'X-API-Key' ausente ou inválido."
            )

        key_hash = self._hash_key(raw_key)
        if key_hash not in self._keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chave de API inválida ou não autorizada."
            )

        key_data = self._keys[key_hash]
        if not key_data.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chave de API desativada ou suspensa por inadimplência."
            )

        # Sliding window rate limiter
        now = time.time()
        tier_cfg = TIER_LIMITS[key_data["tier"]]
        rpm_limit = tier_cfg["rpm"]

        # Remove requisições com mais de 60 segundos
        timestamps = self._request_timestamps[key_hash]
        self._request_timestamps[key_hash] = [ts for ts in timestamps if now - ts < 60.0]

        if len(self._request_timestamps[key_hash]) >= rpm_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite de requisições excedido para o tier {key_data['tier']} ({rpm_limit} req/min). Faça upgrade."
            )

        # Registra timestamp atual e incrementa uso
        self._request_timestamps[key_hash].append(now)
        key_data["total_requests"] += 1
        self._save_keys()

        return key_data

api_key_manager = APIKeyManager()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key_dependency(request: Request) -> Dict[str, Any]:
    """Dependency para injeção rápida de proteção em rotas FastAPI."""
    api_key = request.headers.get("X-API-Key")
    return api_key_manager.validate_and_rate_limit(api_key)
