"""Держит доску свежей: каждые 10 минут пересобирает доску, каждые 30 минут просит рекордеры сделать выгрузку.
Запуск: python scripts/autoupdate.py  (работает вместе с bots_recorder.py run для обоих аккаунтов)
"""
import os, sys, time, subprocess

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(P, 'private', 'bots_export')
BUILD_EVERY, DUMP_EVERY = 10 * 60, 30 * 60


def queue(path, line):
    with open(os.path.join(path, 'commands.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')


last_dump = 0
while True:
    if time.time() - last_dump >= DUMP_EVERY:
        for d in (EXP, os.path.join(EXP, 'lazy')):
            queue(d, 'dump')
        last_dump = time.time()
        time.sleep(180)  # дать рекордерам выгрузить
    subprocess.run([sys.executable, '-X', 'utf8', os.path.join(P, 'scripts', 'build_schemes.py')], capture_output=True, timeout=300)
    time.sleep(BUILD_EVERY)
