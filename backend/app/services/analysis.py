"""Связь исходных строк с вычислениями. Результат всегда содержит происхождение.

Профиль legacy_pd_clock воспроизводит допущения переданного скрипта. Его
использование явно отмечается: справочники не утверждают семантику pd и углов.
Это реальные вычисления на входном файле, а не демонстрационные числа.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from math import isfinite
from uuid import uuid4
from . import legacy_core as core
from .workbooks import read_workbook
from .spatial_groups import calculate_spatial
from .dent_rm3 import calculate_rm3
from .group_forecast import group_category


def text(value):
    return core._as_text(value)


def number(value):
    try:
        return core._as_float(value, 'значение')
    except (ValueError, TypeError):
        return None


def context(row):
    keys = tuple(text(row.get(k)) for k in ('id_mu', 'pass_vtd', 'n_tube'))
    if any(v is None for v in keys):
        raise ValueError('Для привязки нужны id_mu, pass_vtd и n_tube')
    return keys


def import_project(data, filename):
    tables = read_workbook(data)
    project = {'id': uuid4().hex, 'name': filename, 'sha256': sha256(data).hexdigest(),
               'createdAt': datetime.now(timezone.utc).isoformat(), 'profile': 'legacy_pd_clock',
               'assumptions': ['Рабочее давление принято из pd по профилю старого скрипта; смысл поля не подтверждён справочником.',
                               'Угловые поля интерпретируются как десятичные часы 0–12; единицы требуют подтверждения.',
                               'Координата по одометру принята началом дефекта в метрах.'],
               'tables': tables, 'defects': [], 'errors': [], 'summary': {}}
    return analyze_project(project)


def analyze_project(project):
    tables = project['tables']
    errors, defects = [], []
    pipes = defaultdict(list)
    for p in tables['weld']:
        try: pipes[context(p)].append(p)
        except ValueError: pass  # Не служит подходящей трубой; ошибку получит зависящая от неё аномалия.
    seen = set()
    prepared = defaultdict(list)
    for raw in tables['anom']:
        kind = str(raw.get('osob_character', '')).strip().upper()
        if kind not in ('CORR', 'DENT'):
            continue
        record = {'id': f"{raw.get('n_defekta') or 'row'}@{raw['_excel_row']}",
                  'sourceId': text(raw.get('n_defekta')) or '', 'kind': 'dent' if kind == 'DENT' else 'single',
                  'pipeNumber': text(raw.get('n_tube')) or '—', 'positionM': number(raw.get('rasst_do_nach_osob_odom')),
                  'lengthMm': number(raw.get('osob_dlina')), 'widthMm': number(raw.get('osob_shirina')),
                  'depthMm': number(raw.get('osob_glubina')), 'side': text(raw.get('place_on_tube')),
                  'source': {'sheet': 'anom', 'row': raw['_excel_row'], 'fields': raw['_sources']},
                  'raw': {k:v for k,v in raw.items() if not k.startswith('_')},
                  'result': {'status': 'invalid', 'pressureMpa': None, 'category': None, 'messages': []}}
        defects.append(record)
        try:
            key = context(raw)
            identity = (key, record['sourceId'])
            if not record['sourceId'] or identity in seen:
                raise ValueError('Отсутствует или повторяется ID дефекта в одном проходе/трубе')
            seen.add(identity)
            candidates = pipes[key]
            if len(candidates) > 1:
                x = number(raw.get('rasst_do_nach_tube'))
                candidates = [p for p in candidates if x is not None and number(p.get('rasst_do_nach_tube')) == x]
            if len(candidates) != 1:
                raise ValueError('Не найдена однозначная связь с weld')
            pipe = candidates[0]
            sources = {}
            for field in ('diameter','tolschina_sten_tube','predel_prochnosti','pd','koeff_nadegn_n','koeff_nadegn_k1','koeff_nadegn_kh','koeff_uslovii_m'):
                p, a = pipe.get(field), raw.get(field)
                chosen = pipe if p not in (None, '') else raw
                sources[field] = chosen['_sources'].get(field)
                if p not in (None, '') and a not in (None, '') and number(p) != number(a):
                    raise ValueError(f'Конфликт anom/weld: {field} ({a} / {p})')
                if sources[field] and sources[field]['formula']:
                    raise ValueError(f'{field}: формула вместо значения выгрузки')
            record['inputSources'] = sources
            if kind == 'DENT':
                record['result'] = {'status': 'needs_parameters', 'pressureMpa': None, 'category': None,
                                    'messages': ['Требуется выбор применимой РМ и полный набор параметров методики вмятин.'],
                                    'sourceCategory': raw.get('danger')}
                assessment=project.get('dentAssessments',{}).get(record['id'])
                if assessment:
                    result=calculate_rm3(number(sources['diameter']['value']),number(sources['tolschina_sten_tube']['value']),
                                         record['lengthMm'],record['widthMm'],record['depthMm'],True)
                    record['result']={**result,'pressureMpa':None,
                                      'messages':['Основание отсутствия вторичных повреждений: '+assessment['evidence'],
                                                  'Расчёт РМ3 не определяет разрушающее давление.']}
                continue
            for field in ('osob_dlina','osob_glubina'):
                if raw['_sources'].get(field,{}).get('formula'):
                    raise ValueError(f'{field}: формула вместо значения выгрузки')
            inputs, warnings = core.build_inputs(raw, pipe, 'pd')
            core.calculate_single_defect(**inputs)  # Валидация геометрии до проверки взаимодействия.
            if inputs['diameter_mm'] <= 2*inputs['wall_mm']:
                raise ValueError('Наружный диаметр должен превышать удвоенную толщину стенки')
            record['inputs'] = inputs
            record['warnings'] = warnings
            prepared[key].append((raw, pipe, record))
        except (ValueError, TypeError, KeyError) as e:
            record['result']['messages'] = [str(e)]
            errors.append({'row': raw['_excel_row'], 'id': record['sourceId'], 'message': str(e)})
    for key, entries in prepared.items():
        # Неполные данные соседа блокируют заключение об изолированности всей трубы.
        all_corr = [r for r in tables['anom'] if str(r.get('osob_character','')).upper()=='CORR'
                    and tuple(text(r.get(k)) for k in ('id_mu','pass_vtd','n_tube')) == key]
        invalid_neighbors = len(all_corr) != len(entries)
        for raw, pipe, record in entries:
            inputs = record['inputs']
            iso = core.evaluate_isolation(raw, all_corr, inputs['diameter_mm'], inputs['wall_mm'])
            record['isolation'] = {'status':iso.status, 'pairs':[core.asdict(p) for p in iso.pairs]}
            if invalid_neighbors or iso.status == 'undetermined':
                record['result'] = {'status':'needs_parameters','pressureMpa':None,'category':None,
                                    'messages':['Недостаточно данных соседних дефектов для определения взаимодействия.']}
            elif iso.status == 'single':
                calc = core.calculate_single_defect(**inputs)
                danger = core.calculate_danger_single(inputs, calc['p_cr_mpa'])
                record['result'] = {'status':'provisional','pressureMpa':calc['p_cr_mpa'],
                                    'category':danger['danger'], 'messages':project['assumptions'],
                                    'method':'СТО §6.2; приложение В ТЗ', 'steps':calc | danger}
            else:
                record['result'] = {'status':'needs_group','pressureMpa':None,'category':None,
                                    'messages':['Обнаружено взаимодействие. Требуется пространственный расчёт группы по §7.1–7.2.']}
        # Связные компоненты взаимодействия; неизвестные пары блокируют расчёт компоненты.
        pending={r['sourceId']:(raw,r) for raw,_,r in entries if r['result']['status']=='needs_group'}
        while pending:
            seed=next(iter(pending))
            component=set()
            queue=[seed]
            while queue:
                ident=queue.pop()
                if ident in component or ident not in pending:continue
                component.add(ident)
                queue.extend(p['neighbor_defect_id'] for p in pending[ident][1]['isolation']['pairs'] if p['pair_status']=='interacting')
            selected=[pending.pop(i) for i in sorted(component)]
            members=[r for _,r in selected]
            try:
                if any(p['pair_status']=='undetermined' for r in members for p in r['isolation']['pairs']):
                    raise ValueError('Неизвестно взаимодействие группы с соседними дефектами')
                base=members[0]['inputs']
                for member in members[1:]:
                    for field in ('diameter_mm','wall_mm','tensile_mpa','pressure_mpa','n','k1','kh','m'):
                        if member['inputs'][field]!=base[field]:raise ValueError(f'Неоднородная группа: {field}')
                spatial=calculate_spatial([raw for raw,_ in selected],base)
                pressure=spatial['critical']['pressureMpa']
                r1,gamma,k=core._sto_safety_factor(base['tensile_mpa'],base['pressure_mpa'],base['n'],base['k1'],base['kh'],base['m'])
                group={**members[0], 'id':'group:'+members[0]['id'], 'sourceId':'Группа '+','.join(sorted(component)),
                       'kind':'group','members':members,'spatial':spatial,
                       'positionM':min(m['positionM'] for m in members),
                       'lengthMm':max(m['positionM']*1000+m['lengthMm'] for m in members)-min(m['positionM']*1000 for m in members),
                       'widthMm':None, 'depthMm':max(m['depthMm'] for m in members),
                       'result':{'status':'provisional','pressureMpa':pressure,'category':None,
                                 'method':'СТО §7.1–7.2','messages':project['assumptions']+[
                                     'Пространственная схематизация требует независимой верификации. Прогноз категории группы пока не выполнен.'],
                                 'steps':{'R1_mpa':r1,'gamma':gamma,'K_STO':k,'p_allow_mpa':pressure/k,
                                          'critical':spatial['critical'],'windowCount':spatial['windowCount'],'lineCount':spatial['lineCount']}}}
                # Прогноз разрешён только при однородных параметрах всей доступной трубы.
                try:
                    for _,_,neighbor in entries:
                        if any(neighbor['inputs'][f]!=base[f] for f in ('diameter_mm','wall_mm','tensile_mpa','pressure_mpa','n','k1','kh','m')):
                            raise ValueError('Параметры соседей неоднородны: прогноз группы невозможен')
                    forecast=group_category(all_corr,component,base,pressure)
                    group['result']['category']=forecast['category']
                    group['result']['steps']['forecast']=forecast
                    group['result']['messages']=project['assumptions']+[
                        'Прогноз: глубина +0,2 мм/год, длина +4 мм/год; начало дефекта фиксировано. Новые взаимодействия учитываются.',
                        'Пространственная модель и допущение направления роста требуют независимой верификации.']
                except ValueError as e:
                    group['result']['messages'].append(str(e))
                for member in members:
                    member['result']={'status':'group_member','pressureMpa':None,'category':None,'messages':['Рассматривается в составе '+group['sourceId']]}
                defects=[r for r in defects if r['id'] not in {m['id'] for m in members}]
                defects.append(group)
            except ValueError as e:
                for member in members:
                    member['result']={'status':'needs_parameters','pressureMpa':None,'category':None,'messages':[str(e)]}
    project['defects'], project['errors'] = defects, errors
    project['summary'] = {'anomRows':len(tables['anom']), 'weldRows':len(tables['weld']),
                          'defects':len(defects), 'statuses':dict(Counter(d['result']['status'] for d in defects))}
    return project
