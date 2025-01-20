from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.database import redis_client
from app.database import get_user_questions, assign_questions_to_user, cache_all_questions
from urllib.parse import unquote
import json

app = FastAPI()

# Jinja2 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="app/templates")

# 정적 파일 디렉토리 마운트
app.mount("/static", StaticFiles(directory="app/static"), name="static")

cache_all_questions()

@app.get("/exam", response_class=HTMLResponse)
async def exam(request: Request,response: Response, page: int = 1):
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
        "title": "Login"
    })

    # Response 헤더를 TemplateResponse에 복사
    for key, value in response.headers.items():
        template_response.headers[key] = value

    return template_response

@app.get("/result", response_class=HTMLResponse)
async def result(request: Request, response: Response):
    response.set_cookie(key="result", value="true", max_age=3600)
    userid = request.cookies.get("userid", "Guest")  # 기본값은 'Guest'
    name = request.cookies.get("name", "Unknown")    # 기본값은 'Unknown'      # 기본값은 '0'
    decoded_name = unquote(name)
    selected_str = unquote(request.cookies.get("selectedOptions", "[]"))

    data = json.loads(selected_str)
    user_answer_list = list(data.values())
    answer_list = json.loads(redis_client.get(f"user:{userid}:answers"))

    score=0
    for i,j in zip(user_answer_list, answer_list):
        if i==j:
            score += 5

    template_response = templates.TemplateResponse("result.html", {
        "request": request,
        "title": "Result",
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