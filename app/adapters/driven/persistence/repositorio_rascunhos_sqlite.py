# Repositorio SQLite para rascunhos do editor de diagramas (US IN-02).

import sqlite3
import threading
from datetime import datetime
from typing import List, Optional

from app.application.ports.driven.repositorio_rascunhos import RepositorioRascunhos
from app.domain.entidades.rascunho_edicao import RascunhoDiagrama


_SCHEMA = """
CREATE TABLE IF NOT EXISTS rascunhos (
    id TEXT PRIMARY KEY,
    repositorio TEXT NOT NULL,
    branch_base TEXT NOT NULL,
    autor_id TEXT NOT NULL,
    titulo TEXT NOT NULL,
    conteudo_mermaid TEXT NOT NULL,
    descricao_mudanca TEXT NOT NULL DEFAULT '',
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rasc_autor ON rascunhos(autor_id);
CREATE INDEX IF NOT EXISTS idx_rasc_repo ON rascunhos(repositorio);
"""


class RepositorioRascunhosSQLite(RepositorioRascunhos):

    def __init__(self, caminho_db: str):
        self._caminho = caminho_db
        self._conexao = sqlite3.connect(caminho_db, check_same_thread=False)
        self._conexao.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conexao.executescript(_SCHEMA)
            self._conexao.commit()

    def salvar(self, rascunho: RascunhoDiagrama) -> None:
        sql = """
            INSERT INTO rascunhos
                (id, repositorio, branch_base, autor_id, titulo, conteudo_mermaid,
                 descricao_mudanca, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                titulo = excluded.titulo,
                conteudo_mermaid = excluded.conteudo_mermaid,
                descricao_mudanca = excluded.descricao_mudanca,
                atualizado_em = excluded.atualizado_em
        """
        with self._lock:
            self._conexao.execute(sql, (
                rascunho.id, rascunho.repositorio, rascunho.branch_base,
                rascunho.autor_id, rascunho.titulo, rascunho.conteudo_mermaid,
                rascunho.descricao_mudanca,
                rascunho.criado_em.isoformat(), rascunho.atualizado_em.isoformat(),
            ))
            self._conexao.commit()

    def obter(self, rascunho_id: str) -> Optional[RascunhoDiagrama]:
        with self._lock:
            linha = self._conexao.execute(
                "SELECT * FROM rascunhos WHERE id = ?", (rascunho_id,),
            ).fetchone()
        return self._linha_para_entidade(linha) if linha else None

    def listar(
        self,
        autor_id: Optional[str] = None,
        repositorio: Optional[str] = None,
    ) -> List[RascunhoDiagrama]:
        clausulas: list = []
        valores: list = []
        if autor_id is not None:
            clausulas.append("autor_id = ?")
            valores.append(autor_id)
        if repositorio is not None:
            clausulas.append("repositorio = ?")
            valores.append(repositorio)
        sql = "SELECT * FROM rascunhos"
        if clausulas:
            sql += " WHERE " + " AND ".join(clausulas)
        sql += " ORDER BY atualizado_em DESC"
        with self._lock:
            linhas = self._conexao.execute(sql, valores).fetchall()
        return [self._linha_para_entidade(l) for l in linhas]

    def remover(self, rascunho_id: str) -> bool:
        with self._lock:
            cur = self._conexao.execute(
                "DELETE FROM rascunhos WHERE id = ?", (rascunho_id,),
            )
            self._conexao.commit()
            return cur.rowcount > 0

    def fechar(self) -> None:
        with self._lock:
            self._conexao.close()

    @staticmethod
    def _linha_para_entidade(linha: sqlite3.Row) -> RascunhoDiagrama:
        return RascunhoDiagrama(
            id=linha["id"],
            repositorio=linha["repositorio"],
            branch_base=linha["branch_base"],
            autor_id=linha["autor_id"],
            titulo=linha["titulo"],
            conteudo_mermaid=linha["conteudo_mermaid"],
            descricao_mudanca=linha["descricao_mudanca"] or "",
            criado_em=datetime.fromisoformat(linha["criado_em"]),
            atualizado_em=datetime.fromisoformat(linha["atualizado_em"]),
        )
