import unittest
from runtime.router import route_tools
from runtime.tools import ALL_TOOLS

class TestMultilingualSwitching(unittest.TestCase):
    def check_routing(self, query, expected_tools, exact_fallback_check=True):
        tools = route_tools(query, ALL_TOOLS)
        names = [t["function"]["name"] for t in tools]
        for expected in expected_tools:
            self.assertIn(expected, names, f"Query '{query}' failed to route to {expected}. Got {names}")

        # Verify not returning fallback tools by mistake when explicit routing is expected
        is_fallback = set(names) == {"system_health", "get_datetime", "calculator"}
        if exact_fallback_check and expected_tools:
            self.assertFalse(is_fallback, f"Query '{query}' routed to fallback tools incorrectly.")

    # ==========================
    # HINGLISH TESTS
    # ==========================
    def test_hinglish_hardware_telemetry(self):
        self.check_routing("Mera laptop bohot garam ho raha hai check CPU", ["system_health"])
        self.check_routing("Bhai battery kitna percent hai", ["system_health"])
        self.check_routing("System ka ram usage batao", ["system_health"])
        self.check_routing("Power profile ko performance me set kar", ["power_profile"])
        self.check_routing("Kya mera CPU throttle ho raha hai?", ["system_health"])

    def test_hinglish_network_radio(self):
        self.check_routing("Bhai wifi on kar do", ["toggle_wifi"])
        self.check_routing("Bluetooth off kar de battery bacha", ["toggle_bluetooth"])
        self.check_routing("Mera wifi status dikhao", ["toggle_wifi"])
        self.check_routing("Wifi connect nahi ho raha check karo", ["toggle_wifi"])

    def test_hinglish_services(self):
        # Because 'restart' and 'service' and 'status' are loanwords, these pass natively!
        self.check_routing("Pipewire restart maro audio nahi aa raha", ["restart_service", "service_status"])
        self.check_routing("Ollama service ka status kya hai?", ["service_status"])
        self.check_routing("Docker daemon check karo", ["service_status"])

    def test_hinglish_memory_expected_failures(self):
        # 'yaad rakhna' / 'yaad rakh' are not in English memory patterns.
        # Fails because no loan words for memory trigger it, goes to fallback.
        self.check_routing("Mera pet name Milo yaad rakhna", ["memory_set"])
        self.check_routing("Mera favorite editor Vim yaad rakhna", ["memory_set"])
        self.check_routing("Mera name Jules hai yaad rakh", ["memory_set"])
        self.check_routing("Mera default browser bhool jao", ["memory_delete"])

    def test_hinglish_memory_loanwords(self):
        # If English loanwords are used, it works
        self.check_routing("Save my note: dudh lana hai", ["memory_set"])
        self.check_routing("Mera name recall karo", ["memory_get"])

    def test_hinglish_tasks(self):
        self.check_routing("Kal subah 10 baje standup call ka reminder lagao", ["task_add"])
        self.check_routing("Saare tasks list karo", ["task_list"])
        self.check_routing("Naya task add karo meeting", ["task_add"])

    @unittest.expectedFailure
    def test_hinglish_tasks_expected_failures(self):
        # 'Cancel' requires English boundary but 'khatam'/'hatao' misses it
        self.check_routing("Task 5 hata do", ["task_cancel"])
        self.check_routing("Reminder cancela karo", ["task_cancel"]) # 'cancela' fails \bcancel\b

    # ==========================
    # SPANGLISH TESTS
    # ==========================
    def test_spanglish_hardware_telemetry(self):
        self.check_routing("Como esta el CPU?", ["system_health"])
        self.check_routing("Muestra mi battery level", ["system_health"])
        self.check_routing("Chequea la RAM", ["system_health"])
        self.check_routing("Cambia el power profile a performance", ["power_profile"])
        self.check_routing("Dime el battery health de mi pc", ["system_health"])

    def test_spanglish_network_radio(self):
        self.check_routing("Enciende el wifi", ["toggle_wifi"])
        self.check_routing("Apaga el bluetooth para ahorrar bateria", ["toggle_bluetooth"])
        self.check_routing("El bluetooth no funciona", ["toggle_bluetooth"])

    @unittest.expectedFailure
    def test_spanglish_services_expected_failures(self):
        # 'reinicia', 'servicio' are Spanish, misses the regex
        self.check_routing("Por favor reinicia el servicio docker que no responde", ["restart_service"])
        self.check_routing("Cual es el status de tailscale?", ["service_status"]) # 'status de' misses 'status of'
        self.check_routing("El daemon esta muerto", ["service_status"])

    @unittest.expectedFailure
    def test_spanglish_memory_expected_failures(self):
        # 'Recuerda', 'Olvida', 'mi ... es' miss the exact match
        self.check_routing("Recuerda que mi distro favorita es Fedora", ["memory_set"])
        self.check_routing("Olvida mi preference de editor", ["memory_delete"])
        self.check_routing("Cual es mi pet name?", ["memory_get"]) # 'Cual es mi' misses 'What is my'

    def test_spanglish_tasks(self):
        self.check_routing("Añade un reminder para las 5", ["task_add"])
        self.check_routing("Muestra los tasks pendientes", ["task_list"])

    def test_spanglish_tasks_expected_failures(self):
        # 'Cancela', 'Borra' miss 'cancel', 'delete' word boundaries
        self.check_routing("Cancela el task numero 2", ["task_cancel"])
        self.check_routing("Borra el task 1", ["task_cancel"])

    # ==========================
    # MULTILINGUAL MATH
    # ==========================
    def test_multilingual_math_loan(self):
        # Pure math expression triggers calculator directly without word matches
        self.check_routing("10 + 20 calculate karo", ["calculator"], exact_fallback_check=False)
        self.check_routing("Cuanto es 150 / 3?", ["calculator"], exact_fallback_check=False)

    @unittest.expectedFailure
    def test_multilingual_math_word_failures(self):
        # Lacks pure expression and misses 'calculate/math'
        self.check_routing("Calcula cuanto es quince por doscientos", ["calculator"], exact_fallback_check=True)
        self.check_routing("Pachas plus pachas kitna hota hai", ["calculator"], exact_fallback_check=True)

    # ==========================
    # MULTILINGUAL MISC
    # ==========================
    def test_multilingual_misc(self):
        self.check_routing("Kitna time ho raha hai?", ["get_datetime"])
        self.check_routing("Trash empty kar do", ["empty_trash"])
        self.check_routing("Discord launch kar do", ["launch_app"])
        self.check_routing("Vaciar el trash bin", ["empty_trash"])
        self.check_routing("Dime la date de hoy", ["get_datetime"])
        self.check_routing("Que time es?", ["get_datetime"])
        self.check_routing("Launch the app terminal", ["launch_app"])

    def test_spanglish_launch_expected_failures(self):
        # 'Abre' misses 'launch/open/start'
        self.check_routing("Abre firefox", ["launch_app"])
        self.check_routing("Inicia la app de musica", ["launch_app"])


if __name__ == "__main__":
    unittest.main()
