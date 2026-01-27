from app.database.session import get_db
from app.models.container import Container

db = next(get_db())
containers = db.query(Container).filter(
    Container.user_id == 6, 
    Container.status == 'running'
).all()

print(f'\nDatabase shows {len(containers)} running containers for user 6:')
print('='*60)
for c in containers:
    cid = c.container_id[:12] if c.container_id else 'None'
    print(f'  - {c.name} (Docker ID: {cid})')
