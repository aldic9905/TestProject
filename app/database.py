import json
import redis
import random
from app.questions import extract_questions

# Redis 연결
redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)

# excel file path
file_path = "app/questions.xlsx"

problem_count = 50
subject_list = ["기초이론","광ca","동ca","관로","전주-한전공가","시스템"]

mul_easy_problems = []
mul_medium_problems = []
mul_hard_problems = []

sub_easy_problems = []
sub_medium_problems = []
sub_hard_problems = []

def cache_all_questions():
    """문제를 가져와 Redis에 캐싱"""
    """
    문제 데이터 구조
    question:과목명:객관식:문제번호
    {
        "id": 문제번호,
        "text": "문제 내용",
        "option1": "1번답",
        "option2": "2번답",
        "option3": "3번답",
        "option4": "4번답",
        "answer": "정답"
    }

    question:과목명:주관식:문제번호
    {
        "id": 문제번호,
        "text": "문제 내용",
        "answer": "정답"
    }
    """
    question_df = extract_questions(file_path)

    for _, row in question_df.iterrows():
        if row["type"] == "객관식":
            if row["diff"] == "하":
                mul_easy_problems.append([row["subject"],row["id"]])
            elif row["diff"] == "중":
                mul_medium_problems.append([row["subject"],row["id"]])
            else:
                mul_hard_problems.append([row["subject"],row["id"]])

            json_obj = {
                "id": row["id"],  # 문제 번호
                "text": row["text"],  # 문제 내용
                "option1": row["op1"],  # 1번 답변
                "option2": row["op2"],  # 2번 답변
                "option3": row["op3"],  # 3번 답변
                "option4": row["op4"],  # 4번 답변
                "option5": row["op5"],  # 5번 답변
                "answer": row["answer"]  # 정답
            }

        else:
            if row["diff"] == "하":
                sub_easy_problems.append(row["id"])
            elif row["diff"] == "중":
                sub_medium_problems.append(row["id"])
            else:
                sub_hard_problems.append(row["id"])

            json_obj = {
                "id": row["id"],  # 문제 번호
                "text": row["text"],  # 문제 내용
                "answer": row["answer"]  # 정답
            }
        
        redis_client.set(f"question:{row['subject']}:{row['type']}:{row['id']}", json.dumps(json_obj))

    print("Questions stored in Redis.")


def get_user_questions(user_id, question_id):
    question = redis_client.get(f"user:{user_id}:question:{question_id}")
    return json.loads(question)
    

def assign_questions_to_user(user_id):
    if redis_client.exists(f"user:{user_id}:question:1"):
        return 
    """사용자별로 고유한 문제 세트를 할당"""
    random.seed(user_id)  # 사용자 ID를 기반으로 랜덤 시드 설정

    problem_distribution = [
        [3, 2, 0],  # 과목 1
        [7, 4, 1],  # 과목 2
        [5, 2, 1],  # 과목 3
        [4, 1, 1],  # 과목 4
        [4, 1, 1],  # 과목 5
        [1, 1, 1],  # 과목 6
    ]

    mul_question_list=[]
    answer_list=[]

    for subject in range(6):
        hard_count, medium_count, easy_count = problem_distribution[subject]

        # 해당 과목에 맞는 문제만 필터링
        hard_questions = [q[1] for q in mul_hard_problems if q[0] == subject_list[subject]]
        medium_questions = [q[1] for q in mul_medium_problems if q[0] == subject_list[subject]]
        easy_questions = [q[1] for q in mul_easy_problems if q[0] == subject_list[subject]]

        # 문제 수만큼 랜덤 샘플링 (개수보다 적으면 가능한 만큼만 선택)
        selected_mul_hard = random.sample(hard_questions, min(hard_count, len(hard_questions)))
        selected_mul_medium = random.sample(medium_questions, min(medium_count, len(medium_questions)))
        selected_mul_easy = random.sample(easy_questions, min(easy_count, len(easy_questions)))

        mul_question_list += selected_mul_easy + selected_mul_medium + selected_mul_hard

    random.shuffle(mul_question_list)

    sub_question_list = random.sample(sub_easy_problems,min(len(sub_easy_problems),3)) + random.sample(sub_medium_problems,min(len(sub_medium_problems),4)) + random.sample(sub_hard_problems,min(len(sub_hard_problems),3))
    random.shuffle(sub_question_list)

    final_question_list = mul_question_list + sub_question_list

    for id,idx in zip(final_question_list,range(1,51)):
        matching_key = redis_client.scan_iter(f"question:*:*:{id}")
        for key in matching_key:
            question_data = json.loads(redis_client.get(key))
            question_data["id"] = idx
            redis_client.set(f"user:{user_id}:question:{idx}", json.dumps(question_data))
            answer_list.append(json.loads(redis_client.get(key))["answer"])
    print(final_question_list)
    save_user_question(user_id, final_question_list, answer_list)
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
