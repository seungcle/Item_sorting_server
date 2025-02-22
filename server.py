from flask import Flask, request, jsonify
import openai
import os
import json
from dotenv import load_dotenv
from flask_cors import CORS

# 환경 변수 로드
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요!")

app = Flask(__name__)
CORS(app)

# GPT-4를 사용하여 가게 이름 + 품목 리스트를 기반으로 카테고리를 분류
def classify_receipt_gpt4(store_name, product_names):
    client = openai.OpenAI(api_key=API_KEY)

    messages = [
        {"role": "system", "content": "너는 가게 이름과 상품 리스트를 기반으로 가게의 카테고리를 분류하는 AI야."},
        {"role": "user", "content": f"다음 가게와 상품들이 어떤 카테고리에 속하는지 분류해줘.\n"
                                    "가게 이름: " + store_name + "\n"
                                    "상품 리스트: " + ", ".join(product_names) + "\n\n"
                                    "가능한 카테고리는 다음과 같아:\n"
                                    "- 식비 (예: 카페, 음식점, 제과점)\n"
                                    "- 교통비 (예: 버스, 지하철, 택시, 주유소)\n"
                                    "- 숙박비 (예: 호텔, 모텔, 에어비앤비)\n"
                                    "- 전자기기 (예: 전자제품 매장, 컴퓨터 매장)\n"
                                    "- 소모품비 (예: 편의점, 마트, 다이소)\n"
                                    "- 기타\n"
                                    "카테고리 이름만 딱 하나만 출력해줘. 문장 없이, 예를 들어 '식비'처럼."  # 프롬프트 수정
        }
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    # 응답에서 불필요한 공백 제거
    category = response.choices[0].message.content.strip()

    # 혹시 모를 예외 상황 처리 (예: 카테고리 외의 응답이 나오는 경우)
    valid_categories = ["식비", "교통비", "숙박비", "전자기기", "소모품비", "기타"]
    if category not in valid_categories:
        category = "기타"

    return category

# API 엔드포인트: 가게 이름과 상품 리스트를 기반으로 카테고리 분류
@app.route("/classify_receipt", methods=["POST"])
def classify_receipt():
    data = request.json  

    # 필수 데이터 확인
    if "store_name" not in data or "product_names" not in data:
        return jsonify({"error": "store_name과 product_names를 제공해야 합니다."}), 400

    store_name = data["store_name"]
    product_names = data["product_names"]

    # GPT-4로 가게 카테고리 분류 요청
    category = classify_receipt_gpt4(store_name, product_names)

    # jsonify() 대신 json.dumps() 사용하고 ensure_ascii=False 설정
    response = {
        "store_name": store_name,
        "category": category  # 카테고리만 출력
    }
    return app.response_class(
        response=json.dumps(response, ensure_ascii=False),
        mimetype='application/json'
    )

if __name__ == "__main__":
    # Render에서 환경 변수 PORT를 사용하여 포트를 설정
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
