from app import creat_app
import os

# 默认为开发环境，按需求修改
config_name = 'development'

app = creat_app()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, use_reloader=False)
    # app.run()
