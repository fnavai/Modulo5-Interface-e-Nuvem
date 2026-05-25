# Repositorio SQLite para regras arquiteturais (US IN-09).

import json
import sqlite3
import threading
from datetime import datetime
from typing import List, Optional

from app.application.ports.driven.repositorio_regras import RepositorioRegras
from app.domain.entidades.regra_arquitetural import (
    RegraArquitetural,
    Severidade,
    TipoRegra,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS regras_arquiteturais (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL,
    severidade TEXT NOT NULL,
    parametros TEXT NOT NULL DEFAULT '{}',
    mensagem TEXT NOT NULL DEFAULT '',
    ativa INTEGER NOT NULL DEFAULT 1,
    criada_por TEXT NOT NULL,
    criada_em TEXT NOT NULL,
    atualizada_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_regras_ativa ON regras_arquiteturais(ativa);
"""


class RepositorioRegrasSQLite(RepositorioRegras):

    def __init__(self, caminho_db: str):
        self._caminho = caminho_db
        self._conexao = sqlite3.connect(caminho_db, check_same_thread=False)
        self._conexao.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conexao.executescript(_SCHEMA)
            self._conexao.commit()

    def salvar(self, regra: RegraArquitetural) -> None:
        sql = """
            INSERT INTO regras_arquiteturais
                (id, nome, tipo, severidade, parametros, mensagem, ativa,
                 criada_por, criada_em, atualizada_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                nome = excluded.nome,
                severidade = excluded.severidade,
                parametros = excluded.parametros,
                mensagem = excluded.mensagem,
                ativa = excluded.ativa,
                atualizada_em = excluded.atualizada_em
        """
        with self._lock:
            self._conexao.execute(sql, (
                regra.id, regra.nome, regra.tipo.value, regra.severidade.value,
                json.dumps(regra.parametros, ensure_ascii=False),
                regra.mensagem, 1 if regra.ativa else 0,
                regra.criada_por,
                regra.criada_em.isoformat(), regra.atualizada_em.isoformat(),
            ))
            self._conexao.commit()

    def obter(self, regra_id: str) -> Optional[RegraArquitetural]:
        with self._lock:
            linha = self._conexao.execute(
                "SELECT * FROM regras_arquiteturais WHERE id = ?", (regra_id,),
            ).fetchone()
        return self._linha_para_entidade(linha) if linha else None

    def listar(self, ativa: Optional[bool] = None) -> List[RegraArquitetural]:
        if ativa is None:
            sql = "SELECT * FROM regras_arquiteturais ORDER BY criada_em DESC"
            args: tuple = ()
        else:
            sql = "SELECT * FROM regras_arquiteturais WHERE ativa = ? ORDER BY criada_em DESC"
            args = (1 if ativa else 0,)
        with self._lock:
            linhas = self._conexao.execute(sql, args).fetchall()
        return [self._linha_para_entidade(l) for l in linhas]

    def remover(self, regra_id: str) -> bool:
        with self._lock:
            cur = self._conexao.execute(
                "DELETE FROM regras_arquiteturais WHERE id = ?", (regra_id,),
            )
            self._conexao.commit()
            return cur.rowcount > 0

    def fechar(self) -> None:
        with self._lock:
            self._conexao.close()

    @staticmethod
    def _linha_para_entidade(linha: sqlite3.Row) -> RegraArquitetural:
        return RegraArquitetural(
            id=linha["id"],
            nome=linha["nome"],
            tipo=TipoRegra(linha["tipo"]),
            severidade=Severidade(linha["severidade"]),
            parametros=json.loads(linha["parametros"] or "{}"),
            mensagem=linha["mensagem"] or "",
            ativa=bool(linha["ativa"]),
            criada_por=linha["criada_por"],
            criada_em=datetime.fromisoformat(linha["criada_em"]),
            atualizada_em=datetime.fromisoformat(linha["atualizada_em"]),
        )
