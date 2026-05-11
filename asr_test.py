#!/usr/bin/env python3
import asyncio
import json
import os
import sys
import websockets

async def transcribe_audio(audio_path):
    api_key = os.environ.get('DASHSCOPE_API_KEY', 'REDACTED_KEY')
    url = 'wss://dashscope.aliyuncs.com/api-ws/v1/inference/'
    
    async with websockets.connect(url, additional_headers={'Authorization': f'bearer {api_key}'}) as ws:
        task_id = "test12345678901234567890123456789012"
        
        # Send run-task
        run_task = {
            "header": {
                "action": "run-task",
                "task_id": task_id,
                "streaming": "duplex"
            },
            "payload": {
                "task_group": "audio",
                "task": "asr",
                "function": "recognition",
                "model": "fun-asr-realtime",
                "parameters": {
                    "sample_rate": 16000,
                    "format": "wav"
                },
                "input": {}
            }
        }
        await ws.send(json.dumps(run_task))
        
        # Wait for task-started
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('header', {}).get('event') == 'task-started':
                break
        
        # Send audio
        with open(audio_path, 'rb') as f:
            while chunk := f.read(4096):
                await ws.send(chunk)
                await asyncio.sleep(0.05)
        
        # Send finish-task
        finish_task = {
            "header": {
                "action": "finish-task",
                "task_id": task_id,
                "streaming": "duplex"
            },
            "payload": {"input": {}}
        }
        await ws.send(json.dumps(finish_task))
        
        # Collect results
        results = []
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            event = data.get('header', {}).get('event')
            if event == 'result-generated':
                text = data.get('payload', {}).get('output', {}).get('sentence', {}).get('text', '')
                if text:
                    results.append(text)
            elif event == 'task-finished':
                break
            elif event == 'task-failed':
                print(f"Error: {data.get('header', {}).get('error_message')}")
                break
        
        return ' '.join(results)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: asr_test.py <audio_file>")
        sys.exit(1)
    
    result = asyncio.run(transcribe_audio(sys.argv[1]))
    print(f"识别结果：{result}")
