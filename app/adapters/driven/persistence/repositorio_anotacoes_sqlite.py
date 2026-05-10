# Repositorio SQLite para anotacoes em diagramas (US IN-03).
# Indexa @mencoes em tabela auxiliar pra consulta rapida por usuario mencionado.

import sqlite3
import threading
from datetime import datetime
from typing import List, Optional

from app.application.ports.driven.repositorio_anotacoes import RepositorioAnotacoes
from app.domain.entidades.anotacao import Anotacao


_SCHEMA = """
CREATE TABLE IF NOT EXISTS anotacoes (
    id TEXT PRIMARY KEY,
    repositorio TEXT NOT NULL,
    modulo TEXT NOT NULL,
    componente TEXT NOT NULL,
    autor_id TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    parent_id TEXT,
    resolvida INTEGER NOT NULL DEFAULT 0,
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_anot_componente ON anotacoes(repositorio, modulo, componente);
CREATE INDEX IF NOT EXISTS idx_anot_parent ON anotacoes(parent_id);
CREATE INDEX IF NOT EXISTS idx_anot_autor ON anotacoes(autor_id);

CREATE TABLE IF NOT EXISTS mencoes_anotacao (
    anotacao_id TEXT NOT NULL,
    usuario_mencionado TEXT NOT NULL,
    PRIMARY KEY (anotacao_id, usuario_mencionado),
    FOREIGN KEY (anotacao_id) REFERENCES anotacoes(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_mencao_usuario ON mencoes_anotacao(usuario_mencionado);
"""


class RepositorioAnotacoesSQLite(RepositorioAnotacoes):

    def __init__(self, caminho_db: str):
        self._caminho = caminho_db
        self._conexao = sqlite3.connect(caminho_db, check_same_thread=False)
        self._conexao.row_factory = sqlite3.Row
        self._conexao.execute("PRAGMA foreign_keys = ON")
        self._lock = threading.Lock()
        with self._lock:
            self._conexao.executescript(_SCHEMA)
            self._conexao.commit()

    def salvar(self, anotacao: Anotacao) -> None:
        sql = """
            INSERT INTO anotacoes
                (id, repositorio, modulo, componente, autor_id, conteudo,
                 parent_id, resolvida, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                conteudo = excluded.conteudo,
                resolvida = excluded.resolvida,
                atualizado_em = excluded.atualizado_em
        """
        with self._lock:
            self._conexao.execute(sql, (
                anotacao.id, anotacao.repositorio, anotacao.modulo, anotacao.componente,
                anotacao.autor_id, anotacao.conteudo, anotacao.parent_id,
                1 if anotacao.resolvida else 0,
                anotacao.criado_em.isoformat(), anotacao.atualizado_em.isoformat(),
            ))
            # Reindexa mencoes (delete + insert)
            self._conexao.execute(
                "DELETE FROM mencoes_anotacao WHERE anotacao_id = ?", (anotacao.id,),
            )
            for usuario in anotacao.mencoes:
                self._conexao.execute(
                    "INSERT INTO mencoes_anotacao (anotacao_id, usuario_mencionado) VALUES (?, ?)",
                    (anotacao.id, usuario),
                )
            self._conexao.commit()

    def obter(self, anotacao_id: str) -> Optional[Anotacao]:
        with self._lock:
            linha = self._conexao.execute(
                "SELECT * FROM anotacoes WHERE id = ?", (anotacao_id,),
            ).fetchone()
        return self._linha_para_entidade(linha) if linha else None

    def listar(
        self,
        repositorio: Optional[str] = None,
        modulo: Optional[str] = None,
        componente: Optional[str] = None,
        resolvida: Optional[bool] = None,
        autor_id: Optional[str] = None,
    ) -> List[Anotacao]:
        clausulas: list = []
        valores: list = []
        if repositorio is not None:
            clausulas.append("repositorio = ?")
            valores.append(repositorio)
        if modulo is not None:
            clausulas.append("modulo = ?")
            valores.append(modulo)
        if componente is not None:
            clausulas.append("componente = ?")
            valores.append(componente)
        if resolvida is True:
            clausulas.append("resolvida = 1")
        elif resolvida is False:
            clausulas.append("resolvida = 0")
        if autor_id is not None:
            clausulas.append("autor_id = ?")
            valores.append(autor_id)
        sql = "SELECT * FROM anotacoes"
        if clausulas:
            sql += " WHERE " + " AND ".join(clausulas)
        sql += " ORDER BY criado_em DESC"
        with self._lock:
            linhas = self._conexao.execute(sql, valores).fetchall()
        return [self._linha_para_entidade(l) for l in linhas]

    def listar_thread(self, parent_id: str) -> List[Anotacao]:
        with self._lock:
            linhas = self._conexao.execute(
                "SELECT * FROM anotacoes WHERE parent_id = ? ORDER BY criado_em ASC",
                (parent_id,),
            ).fetchall()
        return [self._linha_para_entidade(l) for l in linhas]

    def listar_mencoes_de(self, usuario_id: str) -> List[Anotacao]:
        sql = """
            SELECT a.* FROM anotacoes a
            JOIN mencoes_anotacao m ON m.anotacao_id = a.id
            WHERE m.usuario_mencionado = ?
            ORDER BY a.criado_em DESC
        """
        with self._lock:
            linhas = self._conexao.execute(sql, (usuario_id,)).fetchall()
        return [self._linha_para_entidade(l) for l in linhas]

    def remover(self, anotacao_id: str) -> bool:
        with self._lock:
            cur = self._conexao.execute(
                "DELETE FROM anotacoes WHERE id = ?", (anotacao_id,),
            )
            self._conexao.commit()
            return cur.rowcount > 0

    def fechar(self) -> None:
        with self._lock:
            self._conexao.close()

    @staticmethod
    def _linha_para_entidade(linha: sqlite3.Row) -> Anotacao:
        return Anotacao(
            id=linha["id"],
            repositorio=linha["repositorio"],
            modulo=linha["modulo"],
            componente=linha["componente"],
            autor_id=linha["autor_id"],
            conteudo=linha["conteudo"],
            parent_id=linha["parent_id"],
            resolvida=bool(linha["resolvida"]),
            criado_em=datetime.fromisoformat(linha["criado_em"]),
            atualizado_em=datetime.fromisoformat(linha["atualizado_em"]),
        )
