import unittest
from runtime.tools import ALL_TOOLS
from runtime.router import route_tools

class TestComplexTypoFuzzing(unittest.TestCase):

    def assertToolIn(self, tool_name, tools_list, query):
        names = [t["function"]["name"] for t in tools_list]
        self.assertIn(tool_name, names, f"Expected {tool_name} for query: '{query}'")

    # 1. Omissions
    @unittest.expectedFailure
    def test_omission_emty_tresh(self):
        q = "emty tresh"
        self.assertToolIn("empty_trash", route_tools(q, ALL_TOOLS), q)

    def test_omission_chek_batry(self):
        q = "chek batry"
        self.assertToolIn("system_health", route_tools(q, ALL_TOOLS), q)

    def test_omission_shw_tim(self):
        q = "shw tim"
        self.assertToolIn("get_datetime", route_tools(q, ALL_TOOLS), q)

    def test_omission_calclate_45_plus_10(self):
        q = "calclate 45 + 10"
        self.assertToolIn("calculator", route_tools(q, ALL_TOOLS), q)

    def test_omission_remind_me_2_by_mlk(self):
        q = "remind me 2 by mlk"
        self.assertToolIn("task_add", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_omission_wht_is_my_nam(self):
        q = "wht is my nam"
        self.assertToolIn("memory_get", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_omission_trn_on_blutoth(self):
        q = "trn on blutoth"
        self.assertToolIn("toggle_bluetooth", route_tools(q, ALL_TOOLS), q)

    def test_omission_wht_is_dat(self):
        q = "wht is dat"
        self.assertToolIn("get_datetime", route_tools(q, ALL_TOOLS), q)

    def test_omission_chek_cu_ram(self):
        q = "chek cu ram"
        self.assertToolIn("system_health", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_omission_my_fav_color_blu(self):
        q = "my fav color blu"
        self.assertToolIn("memory_set", route_tools(q, ALL_TOOLS), q)

    # 2. Transpositions & Fat-finger
    @unittest.expectedFailure
    def test_transposition_restrt_pipwire(self):
        q = "restrt pipwire"
        self.assertToolIn("restart_service", route_tools(q, ALL_TOOLS), q)

    def test_transposition_rember_my_nam_is_Kaizen(self):
        q = "rember my nam is Kaizen"
        self.assertToolIn("memory_set", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_transposition_lonch_firefx(self):
        q = "lonch firefx"
        self.assertToolIn("launch_app", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_transposition_check_sttaus_of_dokcer(self):
        q = "check sttaus of dokcer"
        self.assertToolIn("service_status", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_transposition_wihfi_sttaus(self):
        q = "wihfi sttaus"
        self.assertToolIn("toggle_wifi", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_transposition_swtich_to_preformance(self):
        q = "swtich to preformance"
        self.assertToolIn("power_profile", route_tools(q, ALL_TOOLS), q)

    def test_transposition_chek_clcok(self):
        q = "chek clcok"
        self.assertToolIn("get_datetime", route_tools(q, ALL_TOOLS), q)

    def test_transposition_calcualte_10_x_5(self):
        q = "calcualte 10 * 5"
        self.assertToolIn("calculator", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_transposition_opne_calcualtor(self):
        q = "opne calcualtor"
        self.assertToolIn("launch_app", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_transposition_waths_my_naem(self):
        q = "waths my naem"
        self.assertToolIn("memory_get", route_tools(q, ALL_TOOLS), q)

    # 3. Phonetic / Colloquial
    def test_phonetic_chek_cu_and_ram(self):
        q = "chek cu and ram"
        self.assertToolIn("system_health", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_phonetic_powre_profle_to_balnced(self):
        q = "powre profle to balnced"
        self.assertToolIn("power_profile", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_phonetic_restrt_srvice(self):
        q = "restrt srvice docker"
        self.assertToolIn("restart_service", route_tools(q, ALL_TOOLS), q)

    def test_phonetic_wut_time_iz_it(self):
        q = "wut time iz it"
        self.assertToolIn("get_datetime", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_phonetic_iz_blueteeth_on(self):
        q = "iz blueteeth on"
        self.assertToolIn("toggle_bluetooth", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_phonetic_mah_name_iz_jerry(self):
        q = "mah name iz jerry"
        self.assertToolIn("memory_set", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_phonetic_hoo_am_eye(self):
        q = "hoo am eye"
        self.assertToolIn("memory_get", route_tools(q, ALL_TOOLS), q)

    def test_phonetic_kalkulate_won_plus_too(self):
        q = "kalkulate 1 + 2"
        self.assertToolIn("calculator", route_tools(q, ALL_TOOLS), q)

    def test_phonetic_cleer_da_trash(self):
        q = "cleer da trash"
        self.assertToolIn("empty_trash", route_tools(q, ALL_TOOLS), q)

    def test_phonetic_shoo_mee_all_tasks(self):
        q = "shoo mee all tasks"
        self.assertToolIn("task_list", route_tools(q, ALL_TOOLS), q)

    # 4. Slang spelling
    def test_slang_remind_me_2_buy_milk_tmrw(self):
        q = "remind me 2 buy milk tmrw"
        self.assertToolIn("task_add", route_tools(q, ALL_TOOLS), q)

    def test_slang_wots_da_vibes(self): # system health is a fallback tool so this works
        q = "wots da vibes"
        self.assertToolIn("system_health", route_tools(q, ALL_TOOLS), q)

    def test_slang_gimme_da_deets_on_cpu(self):
        q = "gimme da deets on cpu"
        self.assertToolIn("system_health", route_tools(q, ALL_TOOLS), q)

    def test_slang_yeet_da_trash(self):
        q = "yeet da trash"
        self.assertToolIn("empty_trash", route_tools(q, ALL_TOOLS), q)

    def test_slang_wat_day_is_it_my_dude(self):
        q = "wat day is it my dude"
        self.assertToolIn("get_datetime", route_tools(q, ALL_TOOLS), q)

    # 5. Extreme Typos (Expected Failures)
    @unittest.expectedFailure
    def test_extreme_omission_emty_tresh(self):
        q = "mty trsh"
        self.assertToolIn("empty_trash", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_extreme_transposition_wihfi_sttaus(self):
        q = "wfii sttaus"
        self.assertToolIn("toggle_wifi", route_tools(q, ALL_TOOLS), q)

    def test_extreme_phonetic_chek_cu_and_ram(self):
        q = "chk cpoo n ramm"
        self.assertToolIn("system_health", route_tools(q, ALL_TOOLS), q)

    def test_extreme_slang_wots_da_vibes(self):
        q = "wz da vbs"
        self.assertToolIn("system_health", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_extreme_restrt_srvice(self):
        q = "rsrt srvis dokr"
        self.assertToolIn("restart_service", route_tools(q, ALL_TOOLS), q)

    def test_extreme_calclate_45_plus_10(self):
        q = "klklte 45 + 10"
        self.assertToolIn("calculator", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_extreme_powre_profle(self):
        q = "pwr prfl 2 prfrmnc"
        self.assertToolIn("power_profile", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_extreme_memory_get(self):
        q = "hu m i"
        self.assertToolIn("memory_get", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_extreme_memory_set(self):
        q = "mi nm is b0b"
        self.assertToolIn("memory_set", route_tools(q, ALL_TOOLS), q)

    @unittest.expectedFailure
    def test_extreme_task_add(self):
        q = "rmnd m 2 do shp"
        self.assertToolIn("task_add", route_tools(q, ALL_TOOLS), q)

if __name__ == '__main__':
    unittest.main()
