# lambda/index.py
import json
import os
# import boto3
import requests
import re  # 正規表現モジュールをインポート
# from botocore.exceptions import ClientError

# FastAPIのエンドポイントURL
FASTAPI_URL = os.environ.get("FASTAPI_URL","")

def lambda_handler(event, context):
    try:
    
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)

        # 会話履歴を使用
        messages = conversation_history.copy()
        
        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })
        
        # FastAPI用のリクエストペイロードを構築
        request_payload = {
            "messages": messages
        }
        print("Calling FastAPI with payload:", json.dumps(request_payload))
        
        # FastAPIエンドポイントにリクエストを送信
        response = requests.post(FASTAPI_URL, json=request_payload)
        
        # レスポンスを解析
        if response.status_code != 200:
            raise Exception(f"FastAPI returned an error: {response.status_code}, {response.text}")
        
        response_body = response.json()
        print("FastAPI response:", json.dumps(response_body, default=str))
        
        # アシスタントの応答を取得
        assistant_response = response_body.get('response')
        if not assistant_response:
            raise Exception("No response content from the FastAPI model")
        
        # アシスタントの応答を会話履歴に追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })

        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
