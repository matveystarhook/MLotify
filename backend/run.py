import os
import uvicorn
from config import settings

# Запускаем ТОЛЬКО API (без бота)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 Starting API server (BOT DISABLED FOR RAILWAY)")
    print(f"📡 Port: {port}")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )