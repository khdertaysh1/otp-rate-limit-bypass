import unittest
from poc import OTPService, demonstrate

class PoCTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
    def service(self, mode='fixed'):
        service = OTPService(mode, lambda: self.now)
        return service, service.issue()
    def test_source_rotation(self):
        for mode in ('vulnerable', 'fixed'):
            service, challenge = self.service(mode)
            for _ in range(3):
                self.assertEqual(service.verify(challenge,'A','000000').status,'INVALID_OTP')
            self.assertEqual(service.verify(challenge,'A','000000').status,'RATE_LIMITED')
            self.assertEqual(service.verify(challenge,'B','000000').evaluated, mode=='vulnerable')
    def test_reissue_retains_account_budget(self):
        service, challenge = self.service()
        for _ in range(3):
            service.verify(challenge,'A','000000')
        replacement = service.issue()
        self.assertEqual(service.verify(challenge,'A','123456').status,'UNKNOWN_CHALLENGE')
        self.assertEqual(service.verify(replacement,'B','123456').status,'RATE_LIMITED')
        self.now = 60
        self.assertEqual(service.verify(replacement,'B','123456').status,'VERIFIED')
    def test_challenge_budget_survives_window(self):
        service, challenge = self.service()
        for _ in range(3):
            service.verify(challenge,'A','000000')
        self.now = 60
        self.assertEqual(service.verify(challenge,'B','123456').status,'RATE_LIMITED')
    def test_success_is_single_use(self):
        service, challenge = self.service()
        self.assertEqual(service.verify(challenge,'A','123456').status,'VERIFIED')
        self.assertEqual(service.verify(challenge,'B','123456').status,'ALREADY_USED')
    def test_expiry_and_unknown(self):
        service, challenge = self.service()
        self.assertFalse(service.verify('unknown','A','123456').evaluated)
        self.now = 300
        self.assertEqual(service.verify(challenge,'A','123456').status,'EXPIRED')
    def test_evidence(self):
        report = demonstrate()
        self.assertTrue(report['source_change_bypass_observed'])
        self.assertTrue(report['fixed_blocked_source_change'])
        self.assertFalse(report['account_takeover_demonstrated'])
        self.assertEqual([r['evaluated_attempts'] for r in report['results']], [4,3])

if __name__ == '__main__':
    unittest.main()
