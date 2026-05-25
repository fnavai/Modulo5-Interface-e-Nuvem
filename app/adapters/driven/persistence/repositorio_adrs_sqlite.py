# Repositorio SQLite para ADRs e seus vinculos (US IN-07).

import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional

from app.application.ports.driven.repositorio_adrs import RepositorioADRs
from app.domain.entidades.decisao_arquitetural import (
    ADR,
    StatusADR,
    VinculoComponenteADR,
)
from app.domain.excecoes import VinculoDuplicadoError


_SCHEMA = """
CREATE TABLE IF NOT EXISTS adrs (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    contexto TEXT NOT NULL,
    decisao TEXT NOT NULL,
    consequencias TEXT NOT NULL,
    autor_id TEXT NOT NULL,
    status TEXT NOT NULL,
    documento_aprovacao_id TEXT,
    superada_por_id TEXT,
    motivo_descarte TEXT,
    criada_em TEXT NOT NULL,
    atualizada_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_adr_status ON adrs(status);
CREATE INDEX IF NOT EXISTS idx_adr_autor ON adrs(autor_id);

CREATE TABLE IF NOT EXISTS vinculos_adr_componente (
    adr_id TEXT NOT NULL,
    repositorio TEXT NOT NULL,
    modulo TEXT NOT NULL,
    descricao_componente TEXT NOT NULL DEFAULT '',
    criado_em TEXT NOT NULL,
    PRIMARY KEY (adr_id, repositorio, modulo),
    FOREIGN KEY (adr_id) REFERENCES adrs(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_vinc_componente ON vinculos_adr_componente(repositorio, modulo);
"""


class RepositorioADRsSQLite(RepositorioADRs):

    def __init__(self, caminho_db: str):
        self._caminho = caminho_db
        self._conexao = sqlite3.connect(caminho_db, check_same_thread=False)
        self._conexao.row_factory = sqlite3.Row
        self._conexao.execute("PRAGMA foreign_keys = ON")
        self._lock = threading.Lock()
        with self._lock:
            self._conexao.executescript(_SCHEMA)
            self._conexao.commit()

    # --- ADRs ---

    def salvar(self, adr: ADR) -> None:
        sql = """
            INSERT INTO adrs
                (id, titulo, contexto, decisao, consequencias, autor_id, status,
                 documento_aprovacao_id, superada_por_id, motivo_descarte,
                 criada_em, atualizada_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                titulo = excluded.titulo,
                contexto = excluded.contexto,
                decisao = excluded.decisao,
                consequencias = excluded.consequencias,
                status = excluded.status,
                documento_aprovacao_id = excluded.documento_aprovacao_id,
                superada_por_id = excluded.superada_por_id,
                motivo_descarte = excluded.motivo_descarte,
                atualizada_em = excluded.atualizada_em
        """
        with self._lock:
            self._conexao.execute(sql, (
                adr.id, adr.titulo, adr.contexto, adr.decisao, adr.consequencias,
                adr.autor_id, adr.status.value,
                adr.documento_aprovacao_id, adr.superada_por_id, adr.motivo_descarte,
                adr.criada_em.isoformat(), adr.atualizada_em.isoformat(),
            ))
            self._conexao.commit()

    def obter(self, adr_id: str) -> Optional[ADR]:
        with self._lock:
            linha = self._conexao.execute(
                "SELECT * FROM adrs WHERE id = ?", (adr_id,)
            ).fetchone()
        return self._linha_para_adr(linha) if linha else None

    def listar(
        self,
        status: Optional[StatusADR] = None,
        autor_id: Optional[str] = None,
    ) -> List[ADR]:
        clausulas: list = []
        valores: list = []
        if status is not None:
            clausulas.append("status = ?")
            valores.append(status.value)
        if autor_id is not None:
            clausulas.append("autor_id = ?")
            valores.append(autor_id)
        sql = "SELECT * FROM adrs"
        if clausulas:
            sql += " WHERE " + " AND ".join(clausulas)
        sql += " ORDER BY criada_em DESC"
        with self._lock:
            linhas = self._conexao.execute(sql, valores).fetchall()
        return [self._linha_para_adr(l) for l in linhas]

    # --- Vinculos ---

    def vincular(self, vinculo: VinculoComponenteADR) -> None:
        sql = """
            INSERT INTO vinculos_adr_componente
                (adr_id, repositorio, modulo, descricao_componente, criado_em)
            VALUES (?, ?, ?, ?, ?)
        """
        with self._lock:
            try:
                self._conexao.execute(sql, (
                    vinculo.adr_id, vinculo.repositorio, vinculo.modulo,
                    vinculo.descricao_componente, vinculo.criado_em.isoformat(),
                ))
                self._conexao.commit()
            except sqlite3.IntegrityError as e:
                raise VinculoDuplicadoError(
                    f"Vinculo ja existe para ADR={vinculo.adr_id} {vinculo.repositorio}/{vinculo.modulo}"
                ) from e

    def desvincular(self, adr_id: str, repositorio: str, modulo: str) -> bool:
        with self._lock:
            cursor = self._conexao.execute(
                "DELETE FROM vinculos_adr_componente WHERE adr_id=? AND repositorio=? AND modulo=?",
                (adr_id, repositorio, modulo),
            )
            self._conexao.commit()
            return cursor.rowcount > 0

    def listar_vinculos_de_adr(self, adr_id: str) -> List[VinculoComponenteADR]:
        with self._lock:
            linhas = self._conexao.execute(
                "SELECT * FROM vinculos_adr_componente WHERE adr_id=? ORDER BY repositorio, modulo",
                (adr_id,),
            ).fetchall()
        return [self._linha_para_vinculo(l) for l in linhas]

    def listar_adrs_de_componente(self, repositorio: str, modulo: str) -> List[ADR]:
        sql = """
            SELECT a.* FROM adrs a
            JOIN vinculos_adr_componente v ON v.adr_id = a.id
            WHERE v.repositorio = ? AND v.modulo = ?
            ORDER BY a.criada_em DESC
        """
        with self._lock:
            linhas = self._conexao.execute(sql, (repositorio, modulo)).fetchall()
        return [self._linha_para_adr(l) for l in linhas]

    def contar_adrs_por_modulo(
        self, repositorio: str, modulos: List[str],
    ) -> Dict[str, Dict[str, int]]:
        if not modulos:
            return {}
        placeholders = ",".join(["?"] * len(modulos))
        sql = f"""
            SELECT v.modulo, a.status, COUNT(*) as qtd
            FROM vinculos_adr_componente v
            JOIN adrs a ON a.id = v.adr_id
            WHERE v.repositorio = ? AND v.modulo IN ({placeholders})
            GROUP BY v.modulo, a.status
        """
        params = [repositorio, *modulos]
        with self._lock:
            linhas = self._conexao.execute(sql, params).fetchall()
        out: Dict[str, Dict[str, int]] = {}
        for linha in linhas:
            out.setdefault(linha["modulo"], {})[linha["status"]] = linha["qtd"]
        return out

    def fechar(self) -> None:
        with self._lock:
            self._conexao.close()

    # --- Helpers ---

    @staticmethod
    def _linha_para_adr(linha: sqlite3.Row) -> ADR:
        return ADR(
            id=linha["id"],
            titulo=linha["titulo"],
            contexto=linha["contexto"],
            decisao=linha["decisao"],
            consequencias=linha["consequencias"],
            autor_id=linha["autor_id"],
            status=StatusADR(linha["status"]),
            documento_aprovacao_id=linha["documento_aprovacao_id"],
            superada_por_id=linha["superada_por_id"],
            motivo_descarte=linha["motivo_descarte"],
            criada_em=datetime.fromisoformat(linha["criada_em"]),
            atualizada_em=datetime.fromisoformat(linha["atualizada_em"]),
        )

    @staticmethod
    def _linha_para_vinculo(linha: sqlite3.Row) -> VinculoComponenteADR:
        return VinculoComponenteADR(
            adr_id=linha["adr_id"],
            repositorio=linha["repositorio"],
            modulo=linha["modulo"],
            descricao_componente=linha["descricao_componente"] or "",
            criado_em=datetime.fromisoformat(linha["criado_em"]),
        )
