import unittest
from runtime.tools import ALL_TOOLS
from runtime.router import route_tools

class TestMultilingualPersona(unittest.TestCase):
    """
    Stress-Testing synthetic behavioral fuzzing on NanoHat v3.
    Simulating a Multilingual & Hinglish User persona.
    """

    def check_routing(self, query, expected_tools):
        tools = route_tools(query, ALL_TOOLS)
        names = [t["function"]["name"] for t in tools]
        for expected in expected_tools:
            self.assertIn(expected, names, f"Query '{query}' failed to route to {expected}. Got {names}")

    def test_telemetry_power(self):
        # Pillar 1: Telemetry & Power
        cases = [
            ("battery kitni bachi hai", ["system_health"]),
            ("cuanta memoria queda", ["system_health"]),
            ("mera ram clean karo bro", ["system_health"]),
            ("bateria status por favor", ["system_health"]),
            ("cpu kaisa chal raha hai", ["system_health"]),
            ("estado de la bateria", ["system_health"]),
            ("memoria RAM utilizada", ["system_health"]),
            ("power saver mode on kardo", ["power_profile"]),
            ("modo de energia performance", ["power_profile"]),
            ("battery percent batao", ["system_health"]),
        ]
        for q, expected in cases:
            with self.subTest(query=q):
                self.check_routing(q, expected)

    def test_hardware_radios(self):
        # Pillar 2: Hardware & Radios
        cases = [
            ("wifi band kardo please", ["toggle_wifi"]),
            ("apaga el bluetooth", ["toggle_bluetooth"]),
            ("wifi chalu karo", ["toggle_wifi"]),
            ("enciende el wifi", ["toggle_wifi"]),
            ("bluetooth on hai kya", ["toggle_bluetooth"]),
            ("el bluetooth esta prendido", ["toggle_bluetooth"]),
            ("wifi disconnect kar", ["toggle_wifi"]),
            ("conectar wifi", ["toggle_wifi"]),
            ("bt off kardo", ["toggle_bluetooth"]),
            ("wifi status batao", ["toggle_wifi"]),
        ]
        for q, expected in cases:
            with self.subTest(query=q):
                self.check_routing(q, expected)

    def test_services_daemons_supported(self):
        # Pillar 3: Services & Daemons with English loanwords
        cases = [
            ("pipewire restart maro", ["restart_service"]),
            ("ollama restart kardo", ["restart_service"]),
            ("como esta el daemon de bluetooth", ["service_status"]),
            ("systemd status dekho", ["service_status"]),
        ]
        for q, expected in cases:
            with self.subTest(query=q):
                self.check_routing(q, expected)

    @unittest.expectedFailure
    def test_services_daemons_unsupported_idioms(self):
        # Service queries requiring pure non-English semantic translation
        cases = [
            ("ollama chalu hai kya", ["service_status"]),
            ("estado del servicio docker", ["service_status"]),
            ("reinicia el servidor nginx", ["restart_service"]),
            ("wireplumber chal raha hai ya nahi", ["service_status"]),
        ]
        for q, expected in cases:
            with self.subTest(query=q):
                self.check_routing(q, expected)

    @unittest.expectedFailure
    def test_persistent_memory_unsupported_idioms(self):
        # Pillar 4: Persistent Memory (requires multilingual intent extraction)
        cases = [
            ("mera naam yaad rakho Rahul", ["memory_set"]),
            ("mi editor favorito es vim", ["memory_set"]),
            ("kya yaad hai mere bare mein", ["memory_get"]),
            ("quien soy yo", ["memory_get"]),
            ("mera pet name bhool jao", ["memory_delete"]),
            ("borra mis notas", ["memory_delete"]),
            ("sab memories dikhao", ["memory_list"]),
            ("lista todas las memorias", ["memory_list"]),
            ("mera favorite distro kya hai", ["memory_get"]),
        ]
        for q, expected in cases:
            with self.subTest(query=q):
                self.check_routing(q, expected)

    def test_scheduling_housekeeping_supported(self):
        # Pillar 5: Scheduling & Housekeeping with recognized keywords
        cases = [
            ("task add karo: kal subah 9 baje meeting hai", ["task_add"]),
            ("trash empty kardo", ["empty_trash"]),
            ("kitne baje hai", ["get_datetime"]),
            ("que hora es", ["get_datetime"]),
            ("sab tasks dikhao", ["task_list"]),
            ("task 2 cancel kardo", ["task_cancel"]),
            ("calculate karo 5 + 5", ["calculator"]),
            ("cuanto es 10 * 10", ["calculator"]),
        ]
        for q, expected in cases:
            with self.subTest(query=q):
                self.check_routing(q, expected)

    @unittest.expectedFailure
    def test_scheduling_housekeeping_unsupported_idioms(self):
        # Housekeeping queries with pure non-English verbs
        cases = [
            ("basura vaciar", ["empty_trash"]),
            ("lista de tareas", ["task_list"]),
            ("cancela la tarea 1", ["task_cancel"]),
        ]
        for q, expected in cases:
            with self.subTest(query=q):
                self.check_routing(q, expected)

if __name__ == "__main__":
    unittest.main()
