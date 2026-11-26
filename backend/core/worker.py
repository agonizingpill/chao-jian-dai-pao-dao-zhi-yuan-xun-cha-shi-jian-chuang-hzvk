import json
from pathlib import Path
from traceback import print_exc

from core.queueing import QUEUE, broker
from domain.learning import calculate

pulse = Path('/tmp/compute-heartbeat')


def build_record(job):
    """Run one queued job and return its compute record (without persisting)."""
    status = {'owner': job['owner'], 'input': job['input']}
    payload = job['input']
    if isinstance(payload, dict) and payload.get('kind') == 'weight_trial':
        from domain.lead_shifts_service import complete_trial
        result = complete_trial(payload)
    else:
        result = calculate(payload)
    status.update(status='ready', result=result)
    return status


def serve():
    while True:
        broker.ping()
        pulse.touch()
        item = broker.blmove(QUEUE, f'{QUEUE}:processing', timeout=2, src='LEFT', dest='RIGHT')
        if item is None:
            continue
        job = json.loads(item)
        try:
            status = build_record(job)
        except ValueError as exc:
            status = {'owner': job['owner'], 'input': job['input'],
                      'status': 'rejected', 'detail': str(exc)}
        except Exception:
            print_exc()
            status = {'owner': job['owner'], 'input': job['input'],
                      'status': 'rejected', 'detail': '计算失败，请检查输入和 worker 日志'}
        with broker.pipeline() as pipe:
            pipe.set(f'compute:{job["token"]}', json.dumps(status, allow_nan=False), ex=86400)
            pipe.lrem(f'{QUEUE}:processing', 1, item)
            pipe.execute()
        pulse.touch()


if __name__ == '__main__':
    for raw in broker.lrange(f'{QUEUE}:processing', 0, -1):
        with broker.pipeline() as pipe:
            pipe.lpush(QUEUE, raw)
            pipe.lrem(f'{QUEUE}:processing', 1, raw)
            pipe.execute()
    serve()
