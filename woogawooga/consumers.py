import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger('analysis')
channel_layer = get_channel_layer()

class AnalysisProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.group_name = f'analysis_{self.task_id}'
        
        # 그룹에 추가
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket connected for task: {self.task_id}")
    
    async def disconnect(self, close_code):
        # 그룹에서 제거
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected for task: {self.task_id}")
    
    async def receive(self, text_data):
        # 클라이언트에서 메시지를 받을 때 처리 (필요시)
        pass
    
    # 분석 진행률 업데이트 메시지 처리
    async def analysis_progress(self, event):
        await self.send(text_data=json.dumps({
            'type': 'progress',
            'step': event['step'],
            'progress': event['progress'],
            'message': event['message'],
            'step_name': event['step_name']
        }))
    
    # 분석 완료 메시지 처리
    async def analysis_complete(self, event):
        await self.send(text_data=json.dumps({
            'type': 'complete',
            'result': event['result']
        }))
    
    # 분석 오류 메시지 처리
    async def analysis_error(self, event):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': event['message']
        }))

def send_progress_update(task_id, step, progress, message, step_name):
    """분석 진행률 업데이트를 WebSocket으로 전송"""
    if not channel_layer:
        logger.warning("Channel layer not available")
        return
        
    try:
        async_to_sync(channel_layer.group_send)(
            f'analysis_{task_id}',
            {
                'type': 'analysis_progress',
                'step': step,
                'progress': progress,
                'message': message,
                'step_name': step_name
            }
        )
        logger.info(f"Progress update sent for task {task_id}: {step_name} {progress}%")
    except Exception as e:
        logger.error(f"Failed to send progress update: {str(e)}")

def send_analysis_complete(task_id, result):
    """분석 완료를 WebSocket으로 전송"""
    if not channel_layer:
        logger.warning("Channel layer not available")
        return
        
    try:
        async_to_sync(channel_layer.group_send)(
            f'analysis_{task_id}',
            {
                'type': 'analysis_complete',
                'result': result
            }
        )
        logger.info(f"Analysis complete sent for task {task_id}")
    except Exception as e:
        logger.error(f"Failed to send analysis complete: {str(e)}")

def send_analysis_error(task_id, message):
    """분석 오류를 WebSocket으로 전송"""
    if not channel_layer:
        logger.warning("Channel layer not available")
        return
        
    try:
        async_to_sync(channel_layer.group_send)(
            f'analysis_{task_id}',
            {
                'type': 'analysis_error',
                'message': message
            }
        )
        logger.info(f"Analysis error sent for task {task_id}: {message}")
    except Exception as e:
        logger.error(f"Failed to send analysis error: {str(e)}")