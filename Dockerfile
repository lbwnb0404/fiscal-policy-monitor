FROM python:3.11-slim

# 安装中文字体
RUN apt-get update && apt-get install -y fonts-wqy-microhei && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目
COPY . .

# 字体路径适配（Docker 内中文字体位置）
ENV FONT_PATH=/usr/share/fonts/truetype/wqy/wqy-microhei.ttc
ENV PYTHONPATH=/app/py_deps_new
ENV MPLCONFIGDIR=/app/output/tmp

RUN mkdir -p output/tmp data/raw data/reports output/charts output/wechat

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--global.developmentMode=false"]
