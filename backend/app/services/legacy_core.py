from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

_NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"main": _NS_MAIN, "rel": _NS_REL, "pkg": _NS_PKG_REL}


class DataError(ValueError):
    """Ошибка входных данных/структуры выгрузки."""


def _col_to_num(col: str) -> int:
    n = 0
    for ch in col.upper():
        n = n * 26 + ord(ch) - 64
    return n


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    s = str(value).strip()
    return s if s else None


def _as_float(value: Any, field: str) -> float:
    if value is None or value == "":
        raise DataError(f"Не заполнено обязательное поле {field}")
    if isinstance(value, bool):
        raise DataError(f"Поле {field} не является числом: {value!r}")
    if isinstance(value, (int, float)):
        out = float(value)
    else:
        s = str(value).strip().replace(" ", "").replace(",", ".")
        try:
            out = float(s)
        except ValueError as exc:
            raise DataError(f"Поле {field} не является числом: {value!r}") from exc
    if not math.isfinite(out):
        raise DataError(f"Поле {field} должно быть конечным числом")
    return out


def _maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return _as_float(value, "value")
    except DataError:
        return None


class SimpleXlsxReader:
    #Минимальный read-only XLSX reader без внешних зависимостей.

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        if self.path.suffix.lower() != ".xlsx":
            raise DataError("Ожидается файл .xlsx")

    def _sheet_map(self, z: zipfile.ZipFile) -> dict[str, str]:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        relmap = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        result: dict[str, str] = {}
        sheets = wb.find("main:sheets", NS)
        if sheets is None:
            return result
        for sheet in sheets:
            name = sheet.attrib["name"]
            rid = sheet.attrib[f"{{{_NS_REL}}}id"]
            target = relmap[rid]
            if target.startswith("/"):
                target = target.lstrip("/")
            elif not target.startswith("xl/"):
                target = "xl/" + target
            result[name] = target
        return result

    def _shared_strings(self, z: zipfile.ZipFile) -> list[str]:
        if "xl/sharedStrings.xml" not in z.namelist():
            return []
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        values: list[str] = []
        for si in root.findall("main:si", NS):
            parts = [(t.text or "") for t in si.findall(".//main:t", NS)]
            values.append("".join(parts))
        return values

    def sheet_names(self) -> list[str]:
        with zipfile.ZipFile(self.path) as z:
            return list(self._sheet_map(z))

    def read_table(self, sheet_name: str) -> list[dict[str, Any]]:
        with zipfile.ZipFile(self.path) as z:
            sheet_map = self._sheet_map(z)
            if sheet_name not in sheet_map:
                raise DataError(
                    f"В книге нет листа {sheet_name!r}. Доступно: {', '.join(sheet_map)}"
                )
            shared = self._shared_strings(z)
            root = ET.fromstring(z.read(sheet_map[sheet_name]))
            raw_rows: list[tuple[int, dict[int, Any]]] = []
            for row in root.findall(".//main:sheetData/main:row", NS):
                row_no = int(row.attrib["r"])
                values: dict[int, Any] = {}
                for cell in row.findall("main:c", NS):
                    ref = cell.attrib.get("r", "")
                    match = re.match(r"([A-Z]+)(\d+)", ref)
                    if not match:
                        continue
                    col_no = _col_to_num(match.group(1))
                    cell_type = cell.attrib.get("t")
                    value_node = cell.find("main:v", NS)
                    value: Any = None
                    if cell_type == "inlineStr":
                        value = "".join((t.text or "") for t in cell.findall(".//main:t", NS))
                    elif value_node is not None:
                        raw = value_node.text or ""
                        if cell_type == "s":
                            value = shared[int(raw)]
                        elif cell_type == "b":
                            value = raw == "1"
                        elif cell_type in {"str", "e"}:
                            value = raw
                        else:
                            try:
                                num = float(raw)
                                value = int(num) if num.is_integer() else num
                            except ValueError:
                                value = raw
                    values[col_no] = value
                raw_rows.append((row_no, values))

        if not raw_rows:
            return []
        _, header_cells = raw_rows[0]
        headers = {idx: str(val).strip() for idx, val in header_cells.items() if val is not None}
        rows: list[dict[str, Any]] = []
        for row_no, cells in raw_rows[1:]:
            record = {headers[idx]: value for idx, value in cells.items() if idx in headers}
            record["_excel_row"] = row_no
            rows.append(record)
        return rows


@dataclass
class PairIsolation:
    neighbor_defect_id: str | None
    neighbor_excel_row: int | None
    axial_gap_mm: float | None
    circumferential_gap_mm: float | None
    axial_limit_mm: float
    circumferential_limit_mm: float
    pair_status: str
    reason: str


@dataclass
class IsolationResult:
    status: str
    axial_limit_mm: float
    circumferential_limit_mm: float
    pairs: list[PairIsolation]


@dataclass
class GroupCandidate:
    start_index: int
    end_index: int
    defect_ids: list[str]
    length_mm: float
    effective_depth_mm: float
    q: float
    p_cr_mpa: float


def _validate_common_geometry(diameter_mm: float, wall_mm: float, tensile_mpa: float) -> None:
    if not (diameter_mm > wall_mm > 0):
        raise DataError("Требуется D > t > 0")
    if tensile_mpa <= 0:
        raise DataError("Предел прочности должен быть > 0")


def _pressure_for_geometry(
    diameter_mm: float,
    wall_mm: float,
    tensile_mpa: float,
    length_mm: float,
    depth_mm: float,
) -> tuple[float, float]:
    _validate_common_geometry(diameter_mm, wall_mm, tensile_mpa)
    if length_mm <= 0:
        raise DataError("Длина расчетного дефекта должна быть > 0")
    if not (0 <= depth_mm < wall_mm):
        raise DataError("Требуется 0 <= d < t")
    q = math.sqrt(1 + 0.31 * length_mm**2 / (diameter_mm * wall_mm))
    p_cr = (
        2 * wall_mm * tensile_mpa * (1 - depth_mm / wall_mm)
        / ((diameter_mm - wall_mm) * (1 - depth_mm / (wall_mm * q)))
    )
    return q, p_cr


def _sto_safety_factor(
    tensile_mpa: float,
    pressure_mpa: float,
    n: float,
    k1: float,
    kh: float,
    m: float,
) -> tuple[float, float, float]:
    if tensile_mpa <= 0 or pressure_mpa < 0 or min(n, k1, kh, m) <= 0:
        raise DataError("Некорректные прочностные параметры/коэффициенты")
    r1 = m * tensile_mpa / (k1 * kh)
    gamma = 1 - n * pressure_mpa / r1
    if gamma <= 0:
        raise DataError("Получено gamma <= 0; проверьте давление и коэффициенты")
    k_sto = 0.9 * gamma * n * k1 * kh / m
    return r1, gamma, k_sto


def _tz_safety_factor(n: float, k1: float, kh: float, m: float, up: float = 2.33) -> float:
    #Коэффициент K_TZ по приложению В, формулы (В.2)–(В.4).
    if min(n, k1, kh, m) <= 0:
        raise DataError("Коэффициенты n, k1, kh, m должны быть > 0 для K_TZ")
    k0 = 1.0 / k1
    kp = n * kh / m
    a = up / 3.1
    radicand = (1 - k0) ** 2 + (kp - 1) ** 2 - a**2 * (1 - k0) ** 2 * (kp - 1) ** 2
    denominator = 1 - a**2 * (1 - k0) ** 2
    if radicand < -1e-12 or denominator <= 0:
        raise DataError("Некорректные коэффициенты: невозможно вычислить K_TZ")
    return (1 + a * math.sqrt(max(0.0, radicand))) / denominator


def _danger_threshold_mpa(pressure_mpa: float, k_tz: float) -> float:
    return (1.0 + k_tz) / 2.0 * pressure_mpa


def _single_pressure_at_time(inputs: dict[str, float], years: float) -> float:
    length = inputs["length_mm"] + 4.0 * years
    depth = inputs["depth_mm"] + 0.2 * years
    if depth >= inputs["wall_mm"]:
        return 0.0
    return _pressure_for_geometry(
        inputs["diameter_mm"], inputs["wall_mm"], inputs["tensile_mpa"], length, depth
    )[1]


def _group_pressure_at_time(calc: dict[str, Any], years: float) -> float:
    #Прогноз p_r группы: рост каждого схематизированного элемента, зазоры сохраняются.
    items = calc["projection_items"]
    if not items:
        raise DataError("Нет элементов группы для прогноза")
    diameter = calc["diameter_mm"]
    wall = calc["wall_mm"]
    tensile = calc["tensile_mpa"]

    # Исходные непораженные промежутки между элементами последовательности.
    gaps = [max(0.0, items[i + 1]["start_mm"] - items[i]["end_mm"]) for i in range(len(items) - 1)]
    lengths = [x["length_mm"] + 4.0 * years for x in items]
    depths = [x["depth_mm"] + 0.2 * years for x in items]
    if any(d >= wall for d in depths):
        return 0.0

    best = math.inf
    for n_idx in range(len(items)):
        for m_idx in range(n_idx, len(items)):
            length_nm = sum(lengths[n_idx:m_idx + 1]) + sum(gaps[n_idx:m_idx])
            numerator = sum(depths[i] * lengths[i] for i in range(n_idx, m_idx + 1))
            depth_nm = numerator / length_nm
            _, p_nm = _pressure_for_geometry(diameter, wall, tensile, length_nm, depth_nm)
            best = min(best, p_nm)
    return best


def _solve_tno_years(pressure_func, threshold_mpa: float) -> float | None:
    #Решает p_r(T)=threshold методом бисекции. None — пересечение не найдено до 200 лет.
    if pressure_func(0.0) <= threshold_mpa:
        return 0.0
    hi = 1.0
    while hi <= 200.0 and pressure_func(hi) > threshold_mpa:
        hi *= 2.0
    if hi > 200.0:
        hi = 200.0
        if pressure_func(hi) > threshold_mpa:
            return None
    lo = 0.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if pressure_func(mid) > threshold_mpa:
            lo = mid
        else:
            hi = mid
    return hi


def calculate_danger_single(inputs: dict[str, float], p_r_mpa: float) -> dict[str, Any]:
    k_tz = _tz_safety_factor(inputs["n"], inputs["k1"], inputs["kh"], inputs["m"] )
    threshold = _danger_threshold_mpa(inputs["pressure_mpa"], k_tz)
    depth_ratio = inputs["depth_mm"] / inputs["wall_mm"]
    if depth_ratio > 0.5 or p_r_mpa <= threshold:
        return {
            "danger": "A", "K_TZ": k_tz, "danger_threshold_mpa": threshold,
            "p_r_forecast_3y_mpa": None, "tno_years": 0.0,
            "danger_reason": "depth>50%" if depth_ratio > 0.5 else "current_p_r<=threshold",
        }
    forecast = _single_pressure_at_time(inputs, 3.0)
    danger = "B" if forecast <= threshold else "C"
    tno = _solve_tno_years(lambda t: _single_pressure_at_time(inputs, t), threshold)
    if tno is not None and tno < 0.25:
        danger = "A"
        reason = "TNO<3_months"
    else:
        reason = "forecast_3y"
    return {
        "danger": danger, "K_TZ": k_tz, "danger_threshold_mpa": threshold,
        "p_r_forecast_3y_mpa": forecast, "tno_years": tno, "danger_reason": reason,
    }


def calculate_danger_group(calc: dict[str, Any], defect: dict[str, Any]) -> dict[str, Any]:
    k_tz = _tz_safety_factor(calc["n"], calc["k1"], calc["kh"], calc["m"] )
    threshold = _danger_threshold_mpa(calc["pressure_mpa"], k_tz)
    depth = _as_float(defect.get("osob_glubina"), "osob_glubina")
    depth_ratio = depth / calc["wall_mm"]
    if depth_ratio > 0.5 or calc["p_r_mpa"] <= threshold:
        return {
            "danger": "A", "K_TZ": k_tz, "danger_threshold_mpa": threshold,
            "p_r_forecast_3y_mpa": None, "tno_years": 0.0,
            "danger_reason": "depth>50%" if depth_ratio > 0.5 else "current_group_p_r<=threshold",
        }
    forecast = _group_pressure_at_time(calc, 3.0)
    danger = "B" if forecast <= threshold else "C"
    tno = _solve_tno_years(lambda t: _group_pressure_at_time(calc, t), threshold)
    if tno is not None and tno < 0.25:
        danger = "A"
        reason = "TNO<3_months"
    else:
        reason = "forecast_3y_group"
    return {
        "danger": danger, "K_TZ": k_tz, "danger_threshold_mpa": threshold,
        "p_r_forecast_3y_mpa": forecast, "tno_years": tno, "danger_reason": reason,
    }


def calculate_single_defect(
    diameter_mm: float,
    wall_mm: float,
    tensile_mpa: float,
    length_mm: float,
    depth_mm: float,
    pressure_mpa: float,
    n: float,
    k1: float,
    kh: float,
    m: float,
) -> dict[str, float | bool]:
    q, p_cr = _pressure_for_geometry(
        diameter_mm, wall_mm, tensile_mpa, length_mm, depth_mm
    )
    r1, gamma, k_sto = _sto_safety_factor(tensile_mpa, pressure_mpa, n, k1, kh, m)
    p_allow = p_cr / k_sto
    return {
        "Q": q,
        "p_cr_mpa": p_cr,
        "R1_mpa": r1,
        "gamma": gamma,
        "K_STO": k_sto,
        "p_allow_mpa": p_allow,
        "passes": p_allow >= pressure_mpa,
    }


def _same_context(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if _as_text(a.get("n_tube")) != _as_text(b.get("n_tube")):
        return False
    for field in ("id_mu", "pass_vtd"):
        av, bv = _as_text(a.get(field)), _as_text(b.get(field))
        if av is not None and bv is not None and av != bv:
            return False
    return True


def _context_key(row: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    return (_as_text(row.get("n_tube")), _as_text(row.get("id_mu")), _as_text(row.get("pass_vtd")))


def find_pipe_row(defect: dict[str, Any], weld_rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in weld_rows if _same_context(defect, row)]
    if not candidates:
        raise DataError(
            "Не найдена строка weld для дефекта: "
            f"n_tube={defect.get('n_tube')!r}, id_mu={defect.get('id_mu')!r}, "
            f"pass_vtd={defect.get('pass_vtd')!r}"
        )
    if len(candidates) > 1:
        start = _maybe_float(defect.get("rasst_do_nach_tube"))
        if start is not None:
            exact = [
                row for row in candidates
                if (v := _maybe_float(row.get("rasst_do_nach_tube"))) is not None
                and abs(v - start) < 1e-6
            ]
            if len(exact) == 1:
                return exact[0]
        raise DataError(
            f"Для трубы {defect.get('n_tube')!r} найдено несколько строк weld; нужен дополнительный ключ"
        )
    return candidates[0]


def _axial_interval_mm(defect: dict[str, Any]) -> tuple[float, float] | None:
    x = _maybe_float(defect.get("rasst_do_nach_osob_odom"))
    length = _maybe_float(defect.get("osob_dlina"))
    if x is None or length is None or length < 0:
        return None
    start = x * 1000.0
    return start, start + length


def _axial_gap_mm(a: dict[str, Any], b: dict[str, Any]) -> float | None:
    ia, ib = _axial_interval_mm(a), _axial_interval_mm(b)
    if ia is None or ib is None:
        return None
    sa, ea = ia
    sb, eb = ib
    return max(0.0, max(sa, sb) - min(ea, eb))


def _clock_width_matches_record(defect: dict[str, Any], diameter_mm: float) -> bool:
    start = _maybe_float(defect.get("ugol_do_nach_osob"))
    end = _maybe_float(defect.get("ugol_do_konc_osob"))
    width = _maybe_float(defect.get("osob_shirina"))
    if None in (start, end, width):
        return True
    circumference = math.pi * diameter_mm
    delta_hours = (end - start) % 12.0
    delta_hours = min(delta_hours, 12.0 - delta_hours)
    derived_mm = delta_hours / 12.0 * circumference
    tolerance_mm = max(3.0, 0.05 * max(float(width), 1.0))
    return abs(derived_mm - float(width)) <= tolerance_mm


def _circumferential_gap_mm(
    a: dict[str, Any], b: dict[str, Any], diameter_mm: float
) -> float | None:
    center_a = _maybe_float(a.get("ugol_do_center_osob"))
    center_b = _maybe_float(b.get("ugol_do_center_osob"))
    width_a = _maybe_float(a.get("osob_shirina"))
    width_b = _maybe_float(b.get("osob_shirina"))
    if None in (center_a, center_b, width_a, width_b):
        return None
    if float(width_a) < 0 or float(width_b) < 0:
        return None
    if not _clock_width_matches_record(a, diameter_mm) or not _clock_width_matches_record(b, diameter_mm):
        return None
    circumference = math.pi * diameter_mm
    if float(width_a) >= circumference or float(width_b) >= circumference:
        return 0.0
    pos_a = (float(center_a) % 12.0) / 12.0 * circumference
    pos_b = (float(center_b) % 12.0) / 12.0 * circumference
    center_distance = abs(pos_a - pos_b)
    center_distance = min(center_distance, circumference - center_distance)
    return max(0.0, center_distance - 0.5 * (float(width_a) + float(width_b)))


def _interaction_limits(diameter_mm: float, wall_mm: float) -> tuple[float, float]:
    root = math.sqrt(diameter_mm * wall_mm)
    return 2.0 * root, math.pi * root


def pair_interaction(
    a: dict[str, Any], b: dict[str, Any], diameter_mm: float, wall_mm: float
) -> PairIsolation:
    axial_limit, circum_limit = _interaction_limits(diameter_mm, wall_mm)
    axial_gap = _axial_gap_mm(a, b)
    circum_gap: float | None = None
    if axial_gap is not None and axial_gap > axial_limit:
        status, reason = "isolated", "осевой зазор больше порога 6.1"
    else:
        circum_gap = _circumferential_gap_mm(a, b, diameter_mm)
        if circum_gap is not None and circum_gap > circum_limit:
            status, reason = "isolated", "окружной зазор больше порога 6.2"
        elif axial_gap is None or circum_gap is None:
            status, reason = "undetermined", "недостаточно данных для критериев 6.1–6.2"
        else:
            status, reason = "interacting", "оба зазора не превышают пороги 6.1–6.2"
    return PairIsolation(
        neighbor_defect_id=_as_text(b.get("n_defekta")),
        neighbor_excel_row=b.get("_excel_row"),
        axial_gap_mm=axial_gap,
        circumferential_gap_mm=circum_gap,
        axial_limit_mm=axial_limit,
        circumferential_limit_mm=circum_limit,
        pair_status=status,
        reason=reason,
    )


def evaluate_isolation(
    defect: dict[str, Any],
    all_anom_rows: Iterable[dict[str, Any]],
    diameter_mm: float,
    wall_mm: float,
) -> IsolationResult:
    axial_limit, circum_limit = _interaction_limits(diameter_mm, wall_mm)
    pairs: list[PairIsolation] = []
    for neighbor in all_anom_rows:
        if neighbor is defect or not _same_context(defect, neighbor):
            continue
        if str(neighbor.get("osob_character", "")).strip().upper() != "CORR":
            continue
        pairs.append(pair_interaction(defect, neighbor, diameter_mm, wall_mm))
    if any(p.pair_status == "interacting" for p in pairs):
        status = "interacting"
    elif any(p.pair_status == "undetermined" for p in pairs):
        status = "undetermined"
    else:
        status = "single"
    return IsolationResult(status, axial_limit, circum_limit, pairs)


def _value_from_pipe_or_defect(pipe: dict[str, Any], defect: dict[str, Any], field: str) -> Any:
    if pipe.get(field) not in (None, ""):
        return pipe[field]
    return defect.get(field)


def build_inputs(
    defect: dict[str, Any], pipe: dict[str, Any], pressure_field: str = "pd"
) -> tuple[dict[str, float], list[str]]:
    warnings: list[str] = []
    if pressure_field not in {"pd", "maop"}:
        raise DataError("pressure_field должен быть pd или maop")
    pd = _maybe_float(_value_from_pipe_or_defect(pipe, defect, "pd"))
    maop = _maybe_float(_value_from_pipe_or_defect(pipe, defect, "maop"))
    if pd is not None and maop is not None and abs(pd - maop) > 1e-9:
        warnings.append(f"pd={pd:g} и maop={maop:g} МПа различаются; выбран {pressure_field}")
    data = {
        "diameter_mm": _as_float(_value_from_pipe_or_defect(pipe, defect, "diameter"), "diameter"),
        "wall_mm": _as_float(_value_from_pipe_or_defect(pipe, defect, "tolschina_sten_tube"), "tolschina_sten_tube"),
        "tensile_mpa": _as_float(_value_from_pipe_or_defect(pipe, defect, "predel_prochnosti"), "predel_prochnosti"),
        "length_mm": _as_float(defect.get("osob_dlina"), "osob_dlina"),
        "depth_mm": _as_float(defect.get("osob_glubina"), "osob_glubina"),
        "pressure_mpa": _as_float(_value_from_pipe_or_defect(pipe, defect, pressure_field), pressure_field),
        "n": _as_float(_value_from_pipe_or_defect(pipe, defect, "koeff_nadegn_n"), "koeff_nadegn_n"),
        "k1": _as_float(_value_from_pipe_or_defect(pipe, defect, "koeff_nadegn_k1"), "koeff_nadegn_k1"),
        "kh": _as_float(_value_from_pipe_or_defect(pipe, defect, "koeff_nadegn_kh"), "koeff_nadegn_kh"),
        "m": _as_float(_value_from_pipe_or_defect(pipe, defect, "koeff_uslovii_m"), "koeff_uslovii_m"),
    }
    return data, warnings


def _defect_id(row: dict[str, Any]) -> str:
    return _as_text(row.get("n_defekta")) or f"row-{row.get('_excel_row')}"


def _build_interaction_components(
    rows: list[dict[str, Any]], weld_rows: list[dict[str, Any]]
) -> tuple[list[list[dict[str, Any]]], list[dict[str, Any]]]:
    """Строит компоненты графа взаимодействия по 6.1–6.2.

    Возвращает компоненты и список пар с неопределенной геометрией.
    """
    parent = list(range(len(rows)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    undetermined: list[dict[str, Any]] = []
    pipe_cache: dict[tuple[str | None, str | None, str | None], tuple[float, float]] = {}

    for i, a in enumerate(rows):
        key = _context_key(a)
        if key not in pipe_cache:
            pipe = find_pipe_row(a, weld_rows)
            inp, _ = build_inputs(a, pipe)
            pipe_cache[key] = (inp["diameter_mm"], inp["wall_mm"])
        diameter, wall = pipe_cache[key]
        for j in range(i + 1, len(rows)):
            b = rows[j]
            if not _same_context(a, b):
                continue
            pair = pair_interaction(a, b, diameter, wall)
            if pair.pair_status == "interacting":
                union(i, j)
            elif pair.pair_status == "undetermined":
                undetermined.append({
                    "a": _defect_id(a), "b": _defect_id(b),
                    "tube": a.get("n_tube"), "reason": pair.reason,
                })

    groups: dict[int, list[dict[str, Any]]] = {}
    for i, row in enumerate(rows):
        groups.setdefault(find(i), []).append(row)
    components = list(groups.values())
    components.sort(key=lambda c: (str(c[0].get("n_tube")), min(r.get("_excel_row", 0) for r in c)))
    return components, undetermined


def _side_key(value: Any) -> str:
    s = (_as_text(value) or "UNK").upper()
    if s.startswith("EXT"):
        return "EXT"
    if s.startswith("INT"):
        return "INT"
    return "UNK"


def _merged_depth(side_depths: dict[str, float]) -> float:
    ext = side_depths.get("EXT")
    inte = side_depths.get("INT")
    unknown = side_depths.get("UNK")
    if ext is not None and inte is not None:
        base = ext + inte
        return max(base, unknown or 0.0)
    return max(side_depths.values())


def _projection_items(
    component: list[dict[str, Any]], direct_edges: set[frozenset[str]]
) -> list[dict[str, Any]]:
    """Схематизация осевой последовательности для §7.2.

    Пересекающиеся осевые проекции взаимодействующих дефектов объединяются по 7.1.2.4.
    Для EXT+INT применяется сумма глубин по 7.1.2.5.
    """
    raw: list[dict[str, Any]] = []
    for d in component:
        interval = _axial_interval_mm(d)
        if interval is None:
            raise DataError(f"Нет осевой координаты/длины у дефекта {_defect_id(d)}")
        depth = _as_float(d.get("osob_glubina"), "osob_glubina")
        start, end = interval
        raw.append({
            "start": start,
            "end": end,
            "length": end - start,
            "side_depths": {_side_key(d.get("place_on_tube")): depth},
            "ids": [_defect_id(d)],
        })
    raw.sort(key=lambda x: (x["start"], x["end"]))

    merged: list[dict[str, Any]] = []
    for item in raw:
        if not merged:
            merged.append(item)
            continue
        prev = merged[-1]
        connected = any(
            frozenset((pid, nid)) in direct_edges
            for pid in prev["ids"] for nid in item["ids"]
        )
        if connected and item["start"] <= prev["end"]:
            prev["end"] = max(prev["end"], item["end"])
            prev["length"] = prev["end"] - prev["start"]
            for side, depth in item["side_depths"].items():
                prev["side_depths"][side] = max(prev["side_depths"].get(side, 0.0), depth)
            prev["ids"].extend(item["ids"])
        else:
            merged.append(item)

    for item in merged:
        item["depth"] = _merged_depth(item["side_depths"])
    return merged


def calculate_group_component(
    component: list[dict[str, Any]],
    weld_rows: list[dict[str, Any]],
    all_corr: list[dict[str, Any]],
    pressure_field: str,
) -> dict[str, Any]:
    if len(component) < 2:
        raise DataError("Групповой расчет требует минимум два дефекта")

    first = component[0]
    pipe = find_pipe_row(first, weld_rows)
    base, warnings = build_inputs(first, pipe, pressure_field)
    diameter = base["diameter_mm"]
    wall = base["wall_mm"]
    tensile = base["tensile_mpa"]

    # Контроль однородности параметров трубы в группе.
    for d in component[1:]:
        p = find_pipe_row(d, weld_rows)
        inp, w = build_inputs(d, p, pressure_field)
        warnings.extend(w)
        for field in ("diameter_mm", "wall_mm", "tensile_mpa", "pressure_mpa", "n", "k1", "kh", "m"):
            if abs(inp[field] - base[field]) > 1e-9:
                raise DataError(
                    f"В одной взаимодействующей группе различается {field}: "
                    f"{_defect_id(first)}={base[field]}, {_defect_id(d)}={inp[field]}"
                )

    # Нормативные геометрические масштабы §7.1.
    root = math.sqrt(diameter * wall)
    part_length_mm = 5.0 * root
    overlap_mm = 2.5 * root
    projection_step_mm = math.pi * root
    projection_angle_deg = 360.0 * math.sqrt(wall / diameter)

    # Прямые ребра взаимодействия внутри компоненты.
    direct_edges: set[frozenset[str]] = set()
    pair_details: list[dict[str, Any]] = []
    for i, a in enumerate(component):
        for b in component[i + 1:]:
            pair = pair_interaction(a, b, diameter, wall)
            if pair.pair_status == "interacting":
                direct_edges.add(frozenset((_defect_id(a), _defect_id(b))))
                pair_details.append({
                    "a": _defect_id(a), "b": _defect_id(b),
                    "axial_gap_mm": pair.axial_gap_mm,
                    "circumferential_gap_mm": pair.circumferential_gap_mm,
                })

    items = _projection_items(component, direct_edges)
    if not items:
        raise DataError("Не удалось сформировать последовательность группы")

    # Одиночные и все непрерывные сочетания n..m.
    candidates: list[GroupCandidate] = []
    for n in range(len(items)):
        for m in range(n, len(items)):
            length_nm = items[m]["end"] - items[n]["start"]
            if length_nm <= 0:
                raise DataError("Некорректная длина объединенного дефекта")
            numerator = sum(items[i]["depth"] * items[i]["length"] for i in range(n, m + 1))
            depth_nm = numerator / length_nm
            q_nm, p_nm = _pressure_for_geometry(diameter, wall, tensile, length_nm, depth_nm)
            ids: list[str] = []
            for i in range(n, m + 1):
                ids.extend(items[i]["ids"])
            candidates.append(GroupCandidate(n + 1, m + 1, ids, length_nm, depth_nm, q_nm, p_nm))

    critical = min(candidates, key=lambda c: c.p_cr_mpa)
    r1, gamma, k_sto = _sto_safety_factor(
        tensile, base["pressure_mpa"], base["n"], base["k1"], base["kh"], base["m"]
    )
    p_allow = critical.p_cr_mpa / k_sto

    return {
        "mode": "group_7",
        "member_ids": [_defect_id(d) for d in component],
        "tube": first.get("n_tube"),
        "projection_items": [
            {
                "ids": x["ids"],
                "start_mm": x["start"],
                "end_mm": x["end"],
                "length_mm": x["length"],
                "depth_mm": x["depth"],
            }
            for x in items
        ],
        "pair_interactions": pair_details,
        "normative_geometry": {
            "part_length_min_mm": part_length_mm,
            "overlap_mm": overlap_mm,
            "projection_step_mm": projection_step_mm,
            "projection_angle_deg": projection_angle_deg,
        },
        "candidate_count": len(candidates),
        "candidates": [asdict(c) for c in candidates],
        "critical_candidate": asdict(critical),
        "p_r_mpa": critical.p_cr_mpa,
        "diameter_mm": diameter,
        "wall_mm": wall,
        "tensile_mpa": tensile,
        "n": base["n"],
        "k1": base["k1"],
        "kh": base["kh"],
        "m": base["m"],
        "R1_mpa": r1,
        "gamma": gamma,
        "K_STO": k_sto,
        "p_allow_mpa": p_allow,
        "pressure_mpa": base["pressure_mpa"],
        "passes": p_allow >= base["pressure_mpa"],
        "warnings": sorted(set(warnings)),
    }


def _single_result(
    defect: dict[str, Any], pipe: dict[str, Any], pressure_field: str
) -> dict[str, Any]:
    inputs, warnings = build_inputs(defect, pipe, pressure_field)
    calc = calculate_single_defect(**inputs)
    pf_db = _maybe_float(defect.get("pf"))
    return {
        "mode": "single_6",
        "member_ids": [_defect_id(defect)],
        "tube": defect.get("n_tube"),
        "inputs": inputs,
        "p_r_mpa": calc["p_cr_mpa"],
        "R1_mpa": calc["R1_mpa"],
        "gamma": calc["gamma"],
        "K_STO": calc["K_STO"],
        "p_allow_mpa": calc["p_allow_mpa"],
        "pressure_mpa": inputs["pressure_mpa"],
        "passes": calc["passes"],
        "Q": calc["Q"],
        "pf_db_mpa": pf_db,
        "pf_delta_mpa": None if pf_db is None else calc["p_cr_mpa"] - pf_db,
        "warnings": warnings,
    }


def analyze_workbook(workbook: str | Path, pressure_field: str = "pd") -> dict[str, Any]:
    reader = SimpleXlsxReader(workbook)
    sheets = set(reader.sheet_names())
    missing = {"anom", "weld"} - sheets
    if missing:
        raise DataError(f"В книге отсутствуют листы: {', '.join(sorted(missing))}")

    anom = reader.read_table("anom")
    weld = reader.read_table("weld")
    corr = [r for r in anom if str(r.get("osob_character", "")).strip().upper() == "CORR"]
    if not corr:
        raise DataError("На листе anom не найдено ни одной записи CORR")

    components, undetermined_pairs = _build_interaction_components(corr, weld)
    calculations: list[dict[str, Any]] = []
    defect_results: list[dict[str, Any]] = []

    group_no = 0
    for component in components:
        if len(component) == 1:
            d = component[0]
            pipe = find_pipe_row(d, weld)
            inp, _ = build_inputs(d, pipe, pressure_field)
            iso = evaluate_isolation(d, corr, inp["diameter_mm"], inp["wall_mm"])
            if iso.status == "undetermined":
                calc = {
                    "mode": "undetermined",
                    "member_ids": [_defect_id(d)],
                    "tube": d.get("n_tube"),
                    "passes": None,
                    "p_r_mpa": None,
                    "p_allow_mpa": None,
                    "pressure_mpa": inp["pressure_mpa"],
                    "warnings": ["Одиночность нельзя подтвердить из-за пропусков геометрии"],
                }
            else:
                calc = _single_result(d, pipe, pressure_field)
            calculations.append(calc)
            danger = None
            if calc["mode"] == "single_6":
                danger = calculate_danger_single(calc["inputs"], calc["p_r_mpa"])
                calc.update(danger)
            defect_results.append({
                "n_defekta": _defect_id(d),
                "excel_row": d.get("_excel_row"),
                "n_tube": d.get("n_tube"),
                "mode": calc["mode"],
                "group_id": None,
                "p_r_mpa": calc.get("p_r_mpa"),
                "p_allow_mpa": calc.get("p_allow_mpa"),
                "pressure_mpa": calc.get("pressure_mpa"),
                "passes": calc.get("passes"),
                "danger": None if danger is None else danger["danger"],
                "K_TZ": None if danger is None else danger["K_TZ"],
                "p_r_forecast_3y_mpa": None if danger is None else danger["p_r_forecast_3y_mpa"],
                "tno_years": None if danger is None else danger["tno_years"],
            })
        else:
            group_no += 1
            calc = calculate_group_component(component, weld, corr, pressure_field)
            calc["group_id"] = f"G{group_no:02d}"
            calculations.append(calc)
            for d in component:
                danger = calculate_danger_group(calc, d)
                defect_results.append({
                    "n_defekta": _defect_id(d),
                    "excel_row": d.get("_excel_row"),
                    "n_tube": d.get("n_tube"),
                    "mode": "group_7",
                    "group_id": calc["group_id"],
                    "p_r_mpa": calc["p_r_mpa"],
                    "p_allow_mpa": calc["p_allow_mpa"],
                    "pressure_mpa": calc["pressure_mpa"],
                    "passes": calc["passes"],
                    "danger": danger["danger"],
                    "K_TZ": danger["K_TZ"],
                    "p_r_forecast_3y_mpa": danger["p_r_forecast_3y_mpa"],
                    "tno_years": danger["tno_years"],
                })

    defect_results.sort(key=lambda x: x["excel_row"] or 0)
    singles = sum(1 for c in calculations if c["mode"] == "single_6")
    groups = sum(1 for c in calculations if c["mode"] == "group_7")
    group_members = sum(len(c["member_ids"]) for c in calculations if c["mode"] == "group_7")
    undetermined = sum(1 for c in calculations if c["mode"] == "undetermined")
    failed = sum(1 for c in calculations if c.get("passes") is False)
    danger_counts = {letter: sum(1 for r in defect_results if r.get("danger") == letter) for letter in ("A", "B", "C")}

    return {
        "source_file": str(Path(workbook)),
        "pressure_field": pressure_field,
        "summary": {
            "corr_total": len(corr),
            "single_defects": singles,
            "interaction_groups": groups,
            "defects_in_groups": group_members,
            "undetermined_defects": undetermined,
            "calculation_objects": len(calculations),
            "failed_objects": failed,
            "danger_A": danger_counts["A"],
            "danger_B": danger_counts["B"],
            "danger_C": danger_counts["C"],
            "undetermined_pairs": len(undetermined_pairs),
        },
        "undetermined_pairs": undetermined_pairs,
        "defects": defect_results,
        "calculations": calculations,
    }


def select_result(
    analysis: dict[str, Any], defect_id: str | None, excel_row: int | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = analysis["defects"]
    if defect_id is not None:
        rows = [r for r in rows if r["n_defekta"] == str(defect_id)]
    if excel_row is not None:
        rows = [r for r in rows if r["excel_row"] == excel_row]
    if not rows:
        raise DataError("Указанный дефект не найден среди CORR")
    if len(rows) != 1:
        raise DataError("Найдено несколько подходящих записей")
    row = rows[0]
    if row["group_id"]:
        calc = next(c for c in analysis["calculations"] if c.get("group_id") == row["group_id"])
    else:
        calc = next(
            c for c in analysis["calculations"]
            if c["mode"] != "group_7" and row["n_defekta"] in c["member_ids"]
        )
    return row, calc


def _csv_excel_value(value: Any) -> Any:
    # Перевод из csv формата данных в excel
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        text = f"{value:.12g}"
        return text.replace(".", ",")
    return value


def write_csv(analysis: dict[str, Any], path: str | Path) -> None:
    fields = [
        "n_defekta", "excel_row", "n_tube", "mode", "group_id",
        "p_r_mpa", "p_allow_mpa", "pressure_mpa", "passes",
        "danger", "K_TZ", "p_r_forecast_3y_mpa", "tno_years",
    ]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for row in analysis["defects"]:
            writer.writerow({key: _csv_excel_value(row.get(key)) for key in fields})


def _fmt(v: Any, digits: int = 3) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def print_summary(analysis: dict[str, Any]) -> None:
    s = analysis["summary"]
    print(f"Файл: {analysis['source_file']}")
    print(f"Рабочее давление: поле {analysis['pressure_field']}")
    print()
    print("ИТОГ ПО ВЫГРУЗКЕ")
    print(f"  CORR всего:              {s['corr_total']}")
    print(f"  одиночных (§6):          {s['single_defects']}")
    print(f"  групп (§7):              {s['interaction_groups']}")
    print(f"  дефектов внутри групп:   {s['defects_in_groups']}")
    print(f"  неопределенных:          {s['undetermined_defects']}")
    print(f"  не прошли pдоп >= p:     {s['failed_objects']}")
    print(f"  danger A/B/C:            {s['danger_A']}/{s['danger_B']}/{s['danger_C']}")
    print()
    print(f"{'Дефект':>10}  {'Труба':>8}  {'Режим':<9} {'Группа':<6} {'pр, МПа':>10} {'pдоп':>10} {'pраб':>8} {'Danger':>7}  Итог")
    print("-" * 95)
    for r in analysis["defects"]:
        mode = "§6" if r["mode"] == "single_6" else ("§7" if r["mode"] == "group_7" else "?")
        result = "PASS" if r["passes"] is True else ("FAIL" if r["passes"] is False else "?")
        print(
            f"{r['n_defekta']:>10}  {str(r['n_tube']):>8}  {mode:<9} {str(r['group_id'] or '-'): <6} "
            f"{_fmt(r['p_r_mpa']):>10} {_fmt(r['p_allow_mpa']):>10} {_fmt(r['pressure_mpa']):>8} {str(r.get('danger') or '?'):>7}  {result}"
        )
    if s["undetermined_pairs"]:
        print(f"\nВНИМАНИЕ: {s['undetermined_pairs']} пар имеют недостаточно данных для полной проверки 6.1–6.2.")


def print_detail(row: dict[str, Any], calc: dict[str, Any]) -> None:
    print(f"Дефект: {row['n_defekta']} (Excel row {row['excel_row']})")
    print(f"Труба: {row['n_tube']}")
    print(f"Режим: {'одиночный §6' if row['mode']=='single_6' else 'групповой §7' if row['mode']=='group_7' else 'не определен'}")
    if row["group_id"]:
        print(f"Группа: {row['group_id']} -> {', '.join(calc['member_ids'])}")
    print()
    if calc["mode"] == "single_6":
        i = calc["inputs"]
        print(f"Dн={i['diameter_mm']} мм; t={i['wall_mm']} мм; σвр={i['tensile_mpa']} МПа")
        print(f"l={i['length_mm']} мм; d={i['depth_mm']} мм; p={i['pressure_mpa']} МПа")
        print(f"Q={calc['Q']:.6f}")
        print(f"pкр={calc['p_r_mpa']:.6f} МПа")
        if calc.get("pf_db_mpa") is not None:
            print(f"pf(БД)={calc['pf_db_mpa']:.6f} МПа; Δ={calc['pf_delta_mpa']:+.6f} МПа")
    elif calc["mode"] == "group_7":
        print(f"Расчетных непрерывных вариантов: {calc['candidate_count']}")
        crit = calc["critical_candidate"]
        print(f"Опаснейший вариант: {', '.join(crit['defect_ids'])}")
        print(f"l_nm={crit['length_mm']:.3f} мм; d_nm={crit['effective_depth_mm']:.6f} мм")
        print(f"Q_nm={crit['q']:.6f}; pр={crit['p_cr_mpa']:.6f} МПа")
        g = calc["normative_geometry"]
        print(
            "§7.1 масштабы: "
            f"часть >= {g['part_length_min_mm']:.3f} мм; "
            f"перекрытие {g['overlap_mm']:.3f} мм; "
            f"шаг проекций {g['projection_step_mm']:.3f} мм"
        )
    else:
        print("Расчет не выполнен: геометрия не подтверждена.")
        return
    print(f"R1={calc['R1_mpa']:.6f} МПа; gamma={calc['gamma']:.6f}; KСТО={calc['K_STO']:.6f}")
    print(f"pдоп={calc['p_allow_mpa']:.6f} МПа; pраб={calc['pressure_mpa']:.6f} МПа")
    print("Итог:", "КРИТЕРИЙ ВЫПОЛНЕН" if calc["passes"] else "КРИТЕРИЙ НЕ ВЫПОЛНЕН")
    # Категория опасности рассчитывается отдельно от критерия pдоп>=p.
    danger_row = row.get("danger")
    if danger_row:
        print(f"Danger={danger_row}; K_TZ={row['K_TZ']:.6f}; p_r forecast 3y={_fmt(row.get('p_r_forecast_3y_mpa'), 6)} МПа; TNO={_fmt(row.get('tno_years'), 3)} years")
    if calc.get("warnings"):
        print("Предупреждения:")
        for w in calc["warnings"]:
            print(" -", w)


def self_test() -> None:
    #Численные контрольные примеры Е.1 и Е.2 для формул §7.2.
    def calc_sequence(lengths: list[float], depths: list[float], gaps: list[float]) -> tuple[float, list[GroupCandidate]]:
        D, t, s = 1420.0, 18.7, 588.4
        starts = [0.0]
        for i in range(1, len(lengths)):
            starts.append(starts[-1] + lengths[i - 1] + gaps[i - 1])
        items = [
            {"start": starts[i], "end": starts[i] + lengths[i], "length": lengths[i], "depth": depths[i], "ids": [str(i+1)]}
            for i in range(len(lengths))
        ]
        cs: list[GroupCandidate] = []
        for n in range(len(items)):
            for m in range(n, len(items)):
                L = items[m]["end"] - items[n]["start"]
                dep = sum(items[i]["depth"] * items[i]["length"] for i in range(n, m+1)) / L
                q, p = _pressure_for_geometry(D, t, s, L, dep)
                ids = [str(k+1) for k in range(n, m+1)]
                cs.append(GroupCandidate(n+1, m+1, ids, L, dep, q, p))
        best = min(cs, key=lambda c: c.p_cr_mpa)
        return best.p_cr_mpa, cs

    p1, _ = calc_sequence([370, 440], [4.3, 5.9], [110])
    if abs(p1 - 12.828630) > 2e-6:
        raise AssertionError(f"E.1: {p1} != 12.828630")
    p2, c2 = calc_sequence([50, 100, 150, 200], [2, 6, 3, 4], [100, 200, 300])
    best2 = min(c2, key=lambda c: c.p_cr_mpa)
    if abs(p2 - 14.513716) > 2e-6 or best2.defect_ids != ["2", "3", "4"]:
        raise AssertionError(f"E.2: {p2}, {best2.defect_ids}")
    print("SELF-TEST OK: Е.1 и Е.2 воспроизведены.")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="ВТД CORR: автоматический расчет одиночных (§6) и взаимодействующих (§7) дефектов из XLSX"
    )
    p.add_argument("xlsx", nargs="?", help="XLSX с листами anom и weld")
    sel = p.add_mutually_exclusive_group(required=False)
    sel.add_argument("--defect-id", help="Показать подробности конкретного n_defekta")
    sel.add_argument("--excel-row", type=int, help="Показать подробности строки Excel листа anom")
    p.add_argument("--pressure-field", choices=("pd", "maop"), default="pd")
    p.add_argument("--json", action="store_true", help="JSON вместо текстового вывода")
    p.add_argument("--csv", dest="csv_path", help="Сохранить сводку по всем CORR в CSV")
    p.add_argument("--self-test", action="store_true", help="Проверить формулы на примерах Е.1/Е.2")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        if args.self_test:
            self_test()
            if not args.xlsx:
                return 0
        if not args.xlsx:
            raise DataError("Укажите путь к XLSX")
        analysis = analyze_workbook(args.xlsx, args.pressure_field)
        if args.csv_path:
            write_csv(analysis, args.csv_path)
        if args.defect_id is not None or args.excel_row is not None:
            row, calc = select_result(analysis, args.defect_id, args.excel_row)
            if args.json:
                print(json.dumps({"defect": row, "calculation": calc}, ensure_ascii=False, indent=2))
            else:
                print_detail(row, calc)
        else:
            if args.json:
                print(json.dumps(analysis, ensure_ascii=False, indent=2))
            else:
                print_summary(analysis)
                if args.csv_path:
                    print(f"\nCSV: {args.csv_path}")
        return 0
    except (DataError, FileNotFoundError, zipfile.BadZipFile, KeyError, AssertionError) as exc:
        print(f"ОШИБКА: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
