from flask import jsonify, request
from datetime import timedelta

def init_rate_limiter(app):
    @app.before_request
    def check_rate_limit():
        if request.endpoint == 'routes.generate':
            if not hasattr(app, 'redis'):
                raise RuntimeError("Redis no está configurado")
                
            ip = request.remote_addr
            key = f"ratelimit:{ip}"
            
            current = app.redis.get(key)
            if current and int(current) > app.config.get('RATE_LIMIT', 5):
                return jsonify({
                    "error": "Demasiadas solicitudes",
                    "limit": app.config.get('RATE_LIMIT', 5),
                    "reset_in": app.redis.ttl(key)
                }), 429
                
            pipe = app.redis.pipeline()
            pipe.incr(key, 1)
            pipe.expire(key, timedelta(minutes=1))
            pipe.execute()