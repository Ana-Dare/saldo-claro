# SaldoClaro

API REST (FastAPI) e dashboard em Gradio para controle financeiro pessoal.

## Objetivo e problema

Organizar o dinheiro no dia a dia costuma ser difícil quando receitas, despesas e pagamentos pendentes ficam espalhados. Sem uma visão clara do que já entrou, do que ainda falta pagar e do saldo que sobrará no fim do mês, fica mais difícil decidir gastos e evitar surpresas.

O **SaldoClaro** centraliza movimentações e categorias e calcula indicadores mensais — inclusive **saldo previsto** (saldo atual menos despesas pendentes).

## Solução e funcionalidades

| Área | O que faz |
|------|-----------|
| **API** | CRUD de categorias (receita/despesa) e transações (valor, data, status concluída/pendente, tipo). |
| **Dashboard (API)** | Resumo do mês: receitas recebidas, despesas pagas, despesas pendentes, saldo atual, saldo previsto e totais por categoria. |
| **Interface Gradio** | Dashboard único: navegação por mês, cards de resumo, despesas do mês (marcar como paga), histórico de transações e gestão de categorias. |
| **Persistência** | SQLite criado automaticamente em `backend/saldoclaro.db` na primeira subida da API. |
| **Documentação da API** | OpenAPI interativo em `/docs` (Swagger) e `/redoc`. |

A interface consome apenas a API (`frontend/api_client.py` com biblioteca padrão `urllib`); não acessa o banco diretamente.

## Tecnologias utilizadas

- **Python** 3.10+
- **Backend:** FastAPI, Uvicorn, SQLAlchemy 2, Pydantic v2, SQLite (stdlib)
- **Frontend:** Gradio (Blocks), HTTP via `urllib`
- **Testes (opcional):** Pytest, `httpx` (cliente de teste do FastAPI)

## Pré-requisitos

- Python 3.10 ou superior
- `pip` e ambiente virtual (`venv`)

## Instalação

Na raiz do repositório:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --default-timeout=100 -r requirements.txt
```

Em redes lentas, aumente o timeout do `pip` (por exemplo `--default-timeout=200`) se a instalação interromper.

Para desenvolvimento e testes automatizados:

```bash
pip install --default-timeout=100 -r requirements-dev.txt
```

## Executar o backend

Em um terminal, com o venv ativo:

```bash
cd backend
uvicorn app.main:app --reload
```

- **Swagger:** http://127.0.0.1:8000/docs  
- **ReDoc:** http://127.0.0.1:8000/redoc  
- **Saúde:** http://127.0.0.1:8000/health  

O arquivo `saldoclaro.db` é criado em `backend/` na primeira execução.

## Executar o frontend

Com a API em execução, em **outro** terminal, na raiz do projeto e com o venv ativo:

```bash
source .venv/bin/activate
python -m frontend.app
```

- **Interface:** http://127.0.0.1:7860  

Variáveis opcionais:

- `SALDOCLARO_API_URL` — URL da API (padrão `http://127.0.0.1:8000`)
- `SALDOCLARO_API_TIMEOUT` — timeout das requisições em segundos (padrão `15`)

## Testes

Com `requirements-dev.txt` instalado:

```bash
cd backend
pytest -v
```

## Principais endpoints

| Recurso | Caminho |
|--------|---------|
| Categorias | `POST/GET/PUT/DELETE /categories` |
| Movimentações | `POST/GET/PUT/DELETE /transactions` |
| Dashboard | `GET /dashboard?month=&year=` |

## Uso de inteligência artificial

Aproximadamente **40%** do desenvolvimento contou com auxílio de ferramentas de inteligência artificial (planejamento, revisão de código, documentação e ajustes de interface), com revisão e integração manual no repositório.