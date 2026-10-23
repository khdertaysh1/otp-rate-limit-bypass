#!/usr/bin/env python3
"""Offline OTP rate-limit PoC. Python 3.10+, no network dependencies."""
import argparse
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
import hmac
import json
import time

LAB_ACCOUNT = 'alice@example.test'
LAB_OTP = '123456'  # Public synthetic value, not a real credential.

@dataclass
class Result:
    status: str
    evaluated: bool
    source: str
    challenge: str

class OTPService:
    """Single-process teaching model, not a production authentication service."""
    def __init__(self, mode='fixed', clock=time.monotonic):
        if mode not in {'vulnerable', 'fixed'}:
            raise ValueError('Unknown mode')
        self.mode, self.clock = mode, clock
        self.buckets = defaultdict(deque)
        self.sequence, self.current = 0, None

    def issue(self):
        self.sequence += 1
        self.current = {'id': f'lab-{self.sequence}', 'created': self.clock(), 'attempts': 0, 'used': False}
        return self.current['id']  # Account budget is deliberately not reset.

    def allow(self, key):
        now, attempts = self.clock(), self.buckets[key]
        while attempts and now - attempts[0] >= 60:
            attempts.popleft()
        if len(attempts) >= 3:
            return False
        attempts.append(now)
        return True

    def verify(self, challenge, source, otp):
        def result(status, evaluated=False):
            return Result(status, evaluated, source, challenge)
        c = self.current
        if not c or c['id'] != challenge:
            return result('UNKNOWN_CHALLENGE')
        if c['used']:
            return result('ALREADY_USED')
        if self.clock() - c['created'] >= 300:
            return result('EXPIRED')
        if self.mode == 'fixed' and c['attempts'] >= 3:
            return result('RATE_LIMITED')
        key = ('source', source) if self.mode == 'vulnerable' else ('account', LAB_ACCOUNT)
        if not self.allow(key):
            return result('RATE_LIMITED')
        c['attempts'] += 1
        if hmac.compare_digest(str(otp), LAB_OTP):
            c['used'] = True
            return result('VERIFIED', True)
        return result('INVALID_OTP', True)

def demonstrate():
    results = []
    for mode in ('vulnerable', 'fixed'):
        service = OTPService(mode)
        challenge = service.issue()
        rows = [asdict(service.verify(challenge, source, '000000')) for source in ('source-A',)*4 + ('source-B',)]
        results.append({'mode': mode, 'evaluated_attempts': sum(r['evaluated'] for r in rows), 'rows': rows})
    return {'scope': 'offline synthetic model', 'account': LAB_ACCOUNT, 'results': results,
            'source_change_bypass_observed': results[0]['rows'][3]['status'] == 'RATE_LIMITED' and results[0]['rows'][4]['evaluated'],
            'fixed_blocked_source_change': results[1]['rows'][4]['status'] == 'RATE_LIMITED',
            'account_takeover_demonstrated': False}

def interactive(mode):
    service = OTPService(mode)
    challenge = service.issue()
    print(f'Offline {mode}; account: {LAB_ACCOUNT}; challenge: {challenge}; training OTP: {LAB_OTP}')
    print('Commands: check SOURCE CODE | issue | reset | quit')
    while True:
        try:
            parts = input('otp-lab> ').strip().split()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if parts == ['quit']:
            break
        if parts == ['issue']:
            challenge = service.issue()
            print(f'New challenge: {challenge}; account window retained.')
        elif parts == ['reset']:
            service = OTPService(mode)
            challenge = service.issue()
            print('All local state reset.')
        elif len(parts) == 3 and parts[0] == 'check':
            print(json.dumps(asdict(service.verify(challenge, parts[1], parts[2]))))
        elif parts:
            print('Use: check SOURCE CODE | issue | reset | quit')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--mode', choices=('vulnerable', 'fixed'), default='fixed')
    args = parser.parse_args()
    if args.interactive:
        if args.json:
            parser.error('--json is only for the non-interactive demonstration')
        return interactive(args.mode)
    report = demonstrate()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print('OTP RATE LIMIT — OFFLINE PoC\n')
        print(f"{'#':<4}{'Source':<14}{'Vulnerable':<22}Fixed")
        for i, (bad, good) in enumerate(zip(report['results'][0]['rows'], report['results'][1]['rows']), 1):
            print(f"{i:<4}{bad['source']:<14}{bad['status']:<22}{good['status']}")
        print('\nEvaluated attempts: vulnerable=4; fixed=3')
        print('Source change reopened evaluation only in the vulnerable model.')
        print('No correct OTP was tried; no account takeover demonstrated.')
    if not (report['source_change_bypass_observed'] and report['fixed_blocked_source_change']):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
