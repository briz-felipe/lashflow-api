from datetime import datetime, timezone, timedelta
from app.domain.enums import ClientSegment
from app.domain.services.client_service import normalize_phone, calculate_segments


class TestNormalizePhone:
    def test_strips_formatting(self):
        assert normalize_phone("(11) 99999-0000") == "11999990000"

    def test_already_digits(self):
        assert normalize_phone("11999990000") == "11999990000"

    def test_strips_spaces_and_dashes(self):
        assert normalize_phone("11 9 9999-0000") == "11999990000"

    def test_empty_string(self):
        assert normalize_phone("") == ""


class TestCalculateSegments:
    def _now(self):
        return datetime.now(timezone.utc)

    def test_vip_by_appointment_count(self):
        segments = calculate_segments(5, 0, self._now(), now=self._now())
        assert ClientSegment.vip in segments

    def test_vip_by_total_spent(self):
        segments = calculate_segments(1, 100_000, self._now(), now=self._now())
        assert ClientSegment.vip in segments

    def test_not_vip_below_threshold(self):
        segments = calculate_segments(4, 99_999, self._now(), now=self._now())
        assert ClientSegment.vip not in segments

    def test_recorrente(self):
        last = self._now() - timedelta(days=20)
        segments = calculate_segments(2, 0, last, now=self._now())
        assert ClientSegment.recorrente in segments

    def test_not_recorrente_old_appointment(self):
        last = self._now() - timedelta(days=50)
        segments = calculate_segments(2, 0, last, now=self._now())
        assert ClientSegment.recorrente not in segments

    def test_not_recorrente_single_appointment(self):
        last = self._now() - timedelta(days=10)
        segments = calculate_segments(1, 0, last, now=self._now())
        assert ClientSegment.recorrente not in segments

    def test_inativa_no_appointments(self):
        segments = calculate_segments(0, 0, None, now=self._now())
        assert ClientSegment.inativa in segments

    def test_inativa_old_appointment(self):
        last = self._now() - timedelta(days=65)
        segments = calculate_segments(1, 0, last, now=self._now())
        assert ClientSegment.inativa in segments

    def test_not_inativa_recent_appointment(self):
        last = self._now() - timedelta(days=30)
        segments = calculate_segments(3, 0, last, now=self._now())
        assert ClientSegment.inativa not in segments

    def test_volume_segment_from_procedure_name(self):
        last = self._now() - timedelta(days=10)
        segments = calculate_segments(2, 0, last, "Volume Russo", self._now())
        assert ClientSegment.volume in segments

    def test_mega_volume_maps_to_volume_segment(self):
        last = self._now() - timedelta(days=10)
        segments = calculate_segments(2, 0, last, "Mega Volume", self._now())
        assert ClientSegment.volume in segments

    def test_classic_segment_from_procedure_name(self):
        last = self._now() - timedelta(days=10)
        segments = calculate_segments(2, 0, last, "Fio a Fio Classic", self._now())
        assert ClientSegment.classic in segments

    def test_hybrid_segment_from_procedure_name(self):
        last = self._now() - timedelta(days=10)
        segments = calculate_segments(2, 0, last, "Hybrid Lash", self._now())
        assert ClientSegment.hybrid in segments

    def test_no_technique_segment_when_name_unknown(self):
        last = self._now() - timedelta(days=10)
        segments = calculate_segments(2, 0, last, "Remoção de cílios", self._now())
        assert ClientSegment.volume not in segments
        assert ClientSegment.classic not in segments
        assert ClientSegment.hybrid not in segments

    def test_multiple_segments_simultaneously(self):
        # vip + recorrente + volume
        last = self._now() - timedelta(days=10)
        segments = calculate_segments(5, 100_000, last, "Volume", self._now())
        assert ClientSegment.vip in segments
        assert ClientSegment.recorrente in segments
        assert ClientSegment.volume in segments
