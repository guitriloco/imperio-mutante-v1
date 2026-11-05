import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from api_mutante.main import app
from api_mutante.scheduler import scheduler

async def test_scheduler_core():
    print("=" * 68)
    print("         VALIDACAO DO AGENDADOR ASSINCRONO (SCHEDULER)")
    print("=" * 68)

    counter = {"ticks": 0}
    async def sample_task():
        counter["ticks"] += 1
        print(f"      [Tick {counter['ticks']}] Tarefa em background executada!")

    print("[1/3] Iniciando tarefa periodica no AsyncScheduler...")
    scheduler.start_task("teste_ticker", interval_seconds=1, coro_fn=sample_task)

    # Aguarda 2.2 segundos para observar múltiplos ciclos
    await asyncio.sleep(2.2)

    status = scheduler.get_status()
    print(f"\n[2/3] Checando status interno do scheduler:")
    print(f"      Ativo: {status['is_running']}")
    print(f"      Tarefas ativas: {status['active_tasks']}")
    print(f"      Total de ticks executados: {counter['ticks']}")
    assert counter["ticks"] >= 2, "Scheduler não disparou as execuções esperadas!"

    # Parando o agendador
    await scheduler.stop()
    assert not scheduler.is_running, "Scheduler deveria estar parado."
    print("      Agendador finalizado com encerramento limpo.")

    # 3. Teste via rota FastAPI TestClient
    print("\n[3/3] Testando endpoint HTTP GET /v1/scheduler/status...")
    with TestClient(app) as client:
        res = client.get("/v1/scheduler/status")
        assert res.status_code == 200, f"Falha na rota do scheduler: {res.text}"
        data = res.json()
        print(f"      Status HTTP: 200 OK -> Tarefas registradas no app: {data['active_tasks']}")
        assert "scan_unindexed_knowledge" in data["active_tasks"]

    print("\n" + "=" * 68)
    print("      AGENDADOR ASSINCRONO VALIDADO COM SUCESSO TOTAL!")
    print("=" * 68)

if __name__ == "__main__":
    asyncio.run(test_scheduler_core())
