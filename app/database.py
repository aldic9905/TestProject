import json
import redis
import random

# Redis 연결
redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)

problem_count = 20 # 5 10 5

easy_problems = [1,2,3,4,5,6,7,8,9,10,11,12,13]
medium_problems = [14,15,16,17,18,19,20,21,22,23,24]
hard_problems = [25,26,27,28,29,30]

def cache_all_questions():
    """문제를 가져와 Redis에 캐싱"""

    questions = [
        {
            "id": i,
            "text": f"문제 {i}입니다",
            "option1": "1번답",
            "option2": "2번답",
            "option3": "3번답",
            "option4": "4번답",
            "answer": "1",
        }
        for i in range(1, 31)
    ]

    for question in questions:
        redis_client.set(f"question:{question['id']}", json.dumps(question))
print("Questions stored in Redis.")


def get_user_questions(user_id, question_id):
    question = redis_client.get(f"user:{user_id}:question:{question_id}")
    return json.loads(question)
    

def assign_questions_to_user(user_id):
    if redis_client.exists(f"user:{user_id}:question:1"):
        return 
    """사용자별로 고유한 문제 세트를 할당"""
    random.seed(user_id)  # 사용자 ID를 기반으로 랜덤 시드 설정
    # 각 리스트에서 랜덤으로 10개의 번호 선택
    selected_easy = random.sample(easy_problems, min(len(easy_problems), 5))
    selected_medium = random.sample(medium_problems, min(len(medium_problems), 10))
    selected_hard = random.sample(hard_problems, min(len(hard_problems), 5))

    question_list = selected_easy + selected_medium + selected_hard
    random.shuffle(question_list)  # 문제 순서 섞기
    


    answer_list=[]
    for question_id, i in zip(question_list, range(1,problem_count+1)):
        question = redis_client.get(f"question:{question_id}")
        question_data = json.loads(question)
        answer_list.append(question_data["answer"])
        question_data["id"] = i
        redis_client.set(f"user:{user_id}:question:{i}", json.dumps(question_data))
    
    save_user_question(user_id, question_list, answer_list)
    print(f"Questions assigned to user {user_id}")

def save_user_question(user_id, question_list, answer_list):
    user_questions = {
        "question_list": question_list,
        "answer_list": answer_list
    }
    redis_client.set(f"user:{user_id}:question", json.dumps(user_questions))
    print(f"{user_id} User question saved.")

def save_user_info(user_id, question_list, answer_list, user_answer_list, score):
    user_result = {
        "question_list": question_list,
        "answer_list": answer_list,
        "user_answer_list": user_answer_list,
        "score": score
    }
    redis_client.set(f"user:{user_id}:result", json.dumps(user_result))
    print(f"{user_id} User result saved.")
