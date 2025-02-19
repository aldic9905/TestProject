from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.database import redis_client
from app.database import get_user_questions, assign_questions_to_user, cache_all_questions, save_user_info
from urllib.parse import unquote
import json

app = FastAPI()

# Jinja2 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="app/templates")

# 정적 파일 디렉토리 마운트
app.mount("/static", StaticFiles(directory="app/static"), name="static")

def clear_redis_questions():
    keys = redis_client.keys("question:*")
    if keys:
        redis_client.delete(*keys)
    print(f"Deleted {len(keys)} question:* keys from Redis")
    
clear_redis_questions()
cache_all_questions()

@app.get("/exam", response_class=HTMLResponse)
async def exam(request: Request, page: int = 1):
    result = request.cookies.get("result")
    if result == "true":
        return RedirectResponse(url="/result")
    user_id = request.cookies.get("userid")
    assign_questions_to_user(user_id=user_id)

    template_response = templates.TemplateResponse("exam.html", {
        "request": request,
        "title": "Welcome to FastAPI",
        "current_page": page
    })

    return template_response

@app.get("/",response_class=HTMLResponse)
async def login(request: Request, response: Response):
    # 모든 쿠키 가져오기
    cookies = request.cookies

    response_headers = {}
    for cookie_name in cookies:
        response_headers[f"Set-Cookie"] = f"{cookie_name}=; Max-Age=0; Path=/"

    template_response = templates.TemplateResponse("login.html", {
        "request": request,
        "title": "로그인"
    })

    # Response 헤더를 TemplateResponse에 복사
    for key, value in response.headers.items():
        template_response.headers[key] = value

    return template_response

@app.get("/result", response_class=HTMLResponse)
async def result(request: Request, response: Response):
    response.set_cookie(key="result", value="true", max_age=3600)
    userid = request.cookies.get("userid", "None")  # 기본값은 'None'
    name = request.cookies.get("name", "None")    # 기본값은 'None'    
    decoded_name = unquote(name)
    selected_str = unquote(request.cookies.get("selectedOptions", "[]"))

    data = json.loads(selected_str)
    user_answer_list = list(data.values())
    answer_list = json.loads(redis_client.get(f"user:{userid}:question"))["answer_list"]
    question_list = json.loads(redis_client.get(f"user:{userid}:question"))["question_list"]

    score=0
    for i,j in zip(user_answer_list, answer_list):
        if i==j:
            score += 5

    save_user_info(userid, question_list, answer_list, user_answer_list, score)

    template_response = templates.TemplateResponse("result.html", {
        "request": request,
        "title": "결과",
        "userid": userid,
        "name": decoded_name,
        "score": score,
    })
    
    # Response 헤더를 TemplateResponse에 복사
    for key, value in response.headers.items():
        template_response.headers[key] = value

    return template_response

@app.get("/api/questions/{user_id}/{question_id}")
async def fetch_questions(user_id: str, question_id: int):
    """사용자 문제 데이터 반환 API"""
    question = get_user_questions(user_id,question_id)
    return {"question": question}

@app.get("/favicon.ico")
async def ignore_favicon():
    return None

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user_id: str = None):
    # Redis에 저장된 모든 유저 ID 가져오기
    keys = redis_client.keys("user:*:result")
    user_ids = [key.decode("utf-8").split(":")[1] for key in keys]  # 바이트 데이터를 문자열로 변환

    # 선택된 사용자 데이터 가져오기
    if user_id:
        user_data = redis_client.get(f"user:{user_id}:result")
        if user_data:
            user_result = json.loads(user_data)
            question_list = user_result["question_list"]
            answer_list = user_result["answer_list"]
            user_answer_list = user_result["user_answer_list"]
            score = user_result["score"]

            # 결과 묶기
            results = zip(question_list, answer_list, user_answer_list)
        else:
            results = []
            score = "정보 없음"
    else:
        user_id = None
        results = []
        score = None

    # 템플릿 렌더링
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user_ids": user_ids,
        "user_id": user_id,
        "results": results,
        "score": score
    })