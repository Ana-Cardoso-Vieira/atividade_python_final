# Aula 19 — RaspaVoo: webscraping de voos + histórico

Igual à [Aula 17](../Aula17-ge_globo) (GE + histórico), trocando a fonte por **painel de voos** do [FlightAware](https://www.flightaware.com/), com front HTML (**RaspaVoo**).

## Site (render_template)

| Rota | Página |
|------|--------|
| GET `/` | Home — busca + avião |
| POST `/buscar` | Resultado do scraping |
| GET `/historico` | Coletas salvas |
| GET `/historico/<id>` | Detalhe da coleta |

## Dois bancos SQLite

| Arquivo | Uso |
|---------|-----|
| `principal.db` | Bind padrão (reservado; sem tabelas nesta aula) |
| `historico_voos.db` | `ColetaVoo` + `VooInfo` (cada sincronização) |

## API JSON

| Método | Rota |
|--------|------|
| GET | `/api` |
| GET | `/api/voos` |
| POST | `/api/voos/sincronizar` |
| GET | `/api/historico/coletas` |
| GET | `/api/historico/coletas/<id>` |

Query: `?aeroporto=SBGR&tipo=chegadas|partidas|todos`

## Rodar

```powershell
cd flask/Aula19Webscraping
pip install -r requirements.txt
python app.py
```

Abra: http://127.0.0.1:5000

Roteiro: `Aula19.txt`.
