"""Custom error handlers for JSON responses"""
from flask import jsonify

def init_error_handlers(app):
    
    @app.errorhandler(429)
    def rate_limit_handler(e):
        return jsonify({
            "error": "Rate limit exceeded",
            "message": str(e.description) if hasattr(e, 'description') else "Too many requests",
            "retry_after": 60,
            "code": 429
        }), 429
    
    @app.errorhandler(400)
    def bad_request_handler(e):
        return jsonify({
            "error": "Bad request",
            "message": str(e.description) if hasattr(e, 'description') else "Invalid request",
            "code": 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized_handler(e):
        return jsonify({
            "error": "Unauthorized",
            "message": "Valid X-API-Key header required",
            "code": 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden_handler(e):
        return jsonify({
            "error": "Forbidden",
            "message": "You don't have permission to access this resource",
            "code": 403
        }), 403
    
    @app.errorhandler(404)
    def not_found_handler(e):
        return jsonify({
            "error": "Not found",
            "message": "The requested endpoint does not exist",
            "code": 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error_handler(e):
        return jsonify({
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "code": 500
        }), 500
