import json
from datetime import datetime
from uuid import UUID

from backend.domain.entities.secret_dm import SecretDM


class SecretCacheDataMapper:
    @staticmethod
    def entity_to_json(secret: SecretDM) -> dict:
        return json.dumps(
            {
                'uuid': str(secret.uuid),
                'secret': secret.secret.decode(),
                'passphrase': secret.passphrase.decode() if secret.passphrase else None,
                'created_at': secret.created_at.isoformat(),
                'expired_at': secret.expired_at.isoformat() if secret.expired_at else None,
                'is_deleted': secret.is_deleted,
            },
        )

    @staticmethod
    def json_to_entity(data: bytes) -> SecretDM:
        json_data = json.loads(data)

        return SecretDM(
            uuid=UUID(json_data['uuid']),
            secret=json_data['secret'].encode(),
            passphrase=json_data['passphrase'].encode() if json_data['passphrase'] else None,
            created_at=datetime.fromisoformat(json_data['created_at']),
            expired_at=datetime.fromisoformat(json_data['expired_at']) if json_data['expired_at'] else None,
            is_deleted=json_data['is_deleted'],
        )
