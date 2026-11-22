# Automação de bot no WhatsApp

Backend Python de exemplo para consultar uma agenda fictícia e enviar mensagens
explicitamente solicitadas por um cliente confiável. A integração de WhatsApp é
feita pela [Evolution API](https://github.com/EvolutionAPI/evolution-api),
projeto open source separado deste backend. A Evolution API não é a API oficial
do WhatsApp/Meta.

> **Dados de demonstração:** a agenda contém somente nomes fictícios e telefones
> `null`. Não inclua dados pessoais, credenciais, QR codes ou sessões reais no
> repositório público.

## Requisitos

- Docker Desktop com Docker Compose
- Git
- Python 3.11+ apenas para executar o backend fora do Docker

## Configuração segura

1. Copie `.env.example` para `.env`.
2. Preencha `POSTGRES_PASSWORD`, `EVOLUTION_API_KEY` e `BACKEND_API_TOKEN` com
   valores fortes e únicos. Use uma senha PostgreSQL sem caracteres que exijam
   codificação em URL, ou codifique-os na URI do banco.
3. Não compartilhe nem publique `.env`. Ele está no `.gitignore`.
4. Se uma chave ou senha real tiver sido publicada anteriormente, revogue-a e
   crie outra. Remover o segredo do arquivo não invalida a credencial antiga.

O token `BACKEND_API_TOKEN` protege as rotas que enviam mensagens. Clientes
autorizados devem enviar `Authorization: Bearer <token>`. Não coloque esse token
em JavaScript público ou em um aplicativo distribuído ao navegador; use um
proxy/backend confiável para manter o segredo no servidor.

## Executar com Docker Compose

Na raiz do projeto:

```powershell
Copy-Item .env.example .env
# Edite .env e configure os três segredos antes de continuar.
docker compose up --build -d
docker compose ps
```

O backend fica disponível em `http://127.0.0.1:8000` e a Evolution API em
`http://127.0.0.1:8080`. As portas são publicadas apenas na interface local.
O PostgreSQL não publica porta no host. As sessões da Evolution API e os dados
do PostgreSQL ficam em volumes Docker privados, não em `evolution_instances/`.

Para encerrar sem apagar os dados persistentes:

```powershell
docker compose down
```

Não use `docker compose down -v` a menos que queira apagar permanentemente os
volumes de banco e sessão.

## Executar o backend diretamente

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.Main.Main
```

O backend escuta em `127.0.0.1:8000` por padrão. Para escutar em uma interface
externa, configure `BACKEND_API_TOKEN`; sem ele, o servidor recusa iniciar.
Configure `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE_NAME` e `EVOLUTION_API_URL`
no ambiente do processo. O backend não inicia envios automaticamente.

Execute os testes automatizados com:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## Configurar o WhatsApp

Depois que a Evolution API estiver pronta, configure a instância e leia o QR
Code usando os scripts locais:

```powershell
docker compose exec backend python SetupWhatsApp.py
docker compose exec backend python GetQRCode.py
docker compose cp backend:/tmp/qrcode.png .\qrcode.png
```

Os scripts usam as variáveis configuradas no `.env`. O QR code é copiado para
`qrcode.png`, ignorado pelo Git. Trate-o como credencial: qualquer pessoa que o
escaneie pode vincular um dispositivo à conta.

## API HTTP

Base local: `http://127.0.0.1:8000`.

| Método e rota | Descrição |
|---|---|
| `GET /api/health` | Verifica se o backend está ativo. |
| `GET /api/days` | Lista os dias disponíveis. |
| `GET /api/students?day=monday` | Retorna horários e dados fictícios da agenda. |
| `POST /api/messages` | Envia uma mensagem para um telefone informado. |
| `POST /api/messages/absence` | Envia aviso para alunos selecionados da turma. |

As rotas `POST` requerem o token configurado no `.env`:

```http
Authorization: Bearer <BACKEND_API_TOKEN>
Content-Type: application/json
```

Exemplo de envio:

```json
{
  "telephone": "00000000000",
  "message": "Mensagem aprovada pelo usuário."
}
```

O exemplo de telefone é apenas ilustrativo. As entradas da agenda pública têm
`telephone: null`, portanto não podem ser selecionadas para envio. Nenhuma
mensagem é enviada por consultas, inicialização do backend ou seleção de aluno.
Não repita automaticamente chamadas com falha parcial, para evitar duplicidades.

Configure `FRONTEND_ORIGINS` com as origens exatas do cliente web. CORS não
substitui autenticação, e o token não deve ser distribuído em código executado
por navegadores.

## Estrutura

```text
.
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── GetQRCode.py
├── README.md
├── requirements.txt
├── SetupWhatsApp.py
└── src/
    ├── Api/Server.py
    ├── Main/Main.py
    ├── Repository/ListStudant.py
    ├── Service/WhatsappService.py
    └── User/Studant.py
```

O ambiente virtual (`venv/`), estado de WhatsApp/Evolution, QR codes, bancos
locais, logs e arquivos `.env` são excluídos do Git.

## Licença e atribuição

Este repositório documenta a integração com a Evolution API; consulte o
[repositório e a licença da Evolution API](https://github.com/EvolutionAPI/evolution-api)
antes de redistribuir ou operar esse serviço. A API e o WhatsApp são projetos
independentes; verifique os termos e políticas aplicáveis antes de usar.
