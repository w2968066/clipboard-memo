"""
鍓创鏉垮蹇樺綍 鈥?鐭棰戝綍灞忚剼鏈紙鎶栭煶/B绔?灏忕孩涔︾増锛?璇濋: #vibecoding澶ц祻
"""

# ============================================================
# 瑙嗛瑙勬牸寤鸿
# ============================================================
# 鍒嗚鲸鐜? 1080x1920 (绔栧睆) 鎴?1920x1080 (妯睆)
# 鏃堕暱: 45-60 绉?# BGM: 蹇妭濂忕數瀛?lo-fi beat锛屽壀杈戠偣閰嶅悎鎿嶄綔
# 瀛楀箷: 澶у瓧骞曪紝姣忓彞涓嶈秴杩?0涓瓧锛屽叧閿瘝楂樹寒
# ============================================================

class ShortVideoScript:
    def __init__(self):
        self.scenes = []
        self._build_scenes()

    def _build_scenes(self):

        # ---- 閽╁瓙锛?-3绉掞級----
        self.scenes.append({
            "timestamp": "0:00-0:03",
            "duration": "3s",
            "title": "寮洪挬瀛愬紑鍦?,
            "visual": [
                "榛戝睆 + 鐧借壊澶у瓧寮瑰叆: '浣犵殑鎻愮ず璇嶉兘鍘诲摢浜嗭紵'",
                "绱ф帴鐫€寮瑰叆: '澶嶅埗瀹屽氨娑堝け锛?",
                "蹇€熼棯杩?涓秷澶辩殑鎻愮ず璇嶇墖娈?
            ],
            "subtitle": "浣犵殑鎻愮ず璇嶉兘鍘诲摢浜嗭紵| 澶嶅埗瀹屽氨娑堝け锛?,
            "narration": "",
            "bgm_beat": "閲嶆媿钀戒笅"
        })

        # ---- 闂鍏遍福锛?-8绉掞級----
        self.scenes.append({
            "timestamp": "0:03-0:08",
            "duration": "5s",
            "title": "鐥涚偣鍏遍福",
            "visual": [
                "褰曞睆: 鐢ㄦ埛鍦ㄦ祻瑙堝櫒澶嶅埗涓€娈垫彁绀鸿瘝",
                "澶嶅埗鍚庡壀璐存澘琚笅涓€鏉″唴瀹硅鐩?,
                "鐢ㄦ埛琛ㄦ儏鎳婃伡锛堥厤琛ㄦ儏鍖咃級"
            ],
            "subtitle": "鍓创鏉垮彧鑳藉瓨涓€鏉?| 鎵句笉鍒颁簡锛?,
            "narration": "",
            "bgm_beat": "蹇妭濂忓垏鐗?
        })

        # ---- 浜у搧浜浉锛?-12绉掞級----
        self.scenes.append({
            "timestamp": "0:08-0:12",
            "duration": "4s",
            "title": "浜у搧浜浉",
            "visual": [
                "鎸?Ctrl+Shift+V锛屾诞绐椾互缂╂斁鍔ㄧ敾寮瑰嚭",
                "榛戣壊鑳屾櫙 + 钃濊壊寮鸿皟鑹茬殑绐楀彛",
                "鍒楄〃涓凡鏈夊涓巻鍙叉潯鐩?
            ],
            "subtitle": "鎸?Ctrl+Shift+V | 鍓创鏉垮巻鍙插叏鍦ㄨ繖",
            "narration": "",
            "bgm_beat": "drop 钀戒笅"
        })

        # ---- 鏍稿績鍗栫偣1锛氭櫤鑳藉垎绫伙紙12-18绉掞級----
        self.scenes.append({
            "timestamp": "0:12-0:18",
            "duration": "6s",
            "title": "鏅鸿兘鍒嗙被",
            "visual": [
                "澶嶅埗涓€娈垫彁绀鸿瘝: '甯垜鍐欎竴涓狿ython鐖櫕...'",
                "娴獥鑷姩鍒锋柊锛屾柊鏉＄洰鍑虹幇鍦ㄩ《閮?,
                "馃摉 鏍囪瘑鑷姩鍙樹寒锛坅ccent鑹诧級",
                "鍒囨崲 2Prompt / 3鍥剧墖 鏍囩锛屽唴瀹硅嚜鍔ㄥ綊绫?
            ],
            "subtitle": "鑷姩璇嗗埆鎻愮ず璇?| 涓€閿垎绫?| 鏈湴杩愯闆朵笂浼?,
            "narration": "",
            "bgm_beat": "杩炵画鍒囩墖"
        })

        # ---- 鏍稿績鍗栫偣2锛氬揩閫熷垎绫绘ā寮忥紙18-26绉掞級----
        self.scenes.append({
            "timestamp": "0:18-0:26",
            "duration": "8s",
            "title": "鎮仠鍒嗙被",
            "visual": [
                "鐐瑰嚮搴曢儴'鍒嗙被'鎸夐挳",
                "榧犳爣鎮仠鍦ㄦ湭鍒嗙被鏉＄洰涓婏紝楂樹寒鏄剧ず",
                "鎸?2 鈫?鏉＄洰鍒嗙被涓?Prompt",
                "馃摉 鐬棿鍙樹寒锛堝崟鏉″埛鏂帮紝涓嶅崱椤匡級",
                "鎸?1 鈫?猸愶笍 鍑虹幇锛堟敹钘忥級",
                "鎸?Backspace 鈫?鏉＄洰鍒犻櫎"
            ],
            "subtitle": "鎮仠 + 鏁板瓧閿?| 1鏀惰棌 2Prompt 3鍥剧墖 4鍒犻櫎 | Backspace鐩存帴鍒?,
            "narration": "",
            "bgm_beat": "鑺傚鍔犻€?
        })

        # ---- 鏍稿績鍗栫偣3锛氬浘鐗囨崟鑾凤紙26-32绉掞級----
        self.scenes.append({
            "timestamp": "0:26-0:32",
            "duration": "6s",
            "title": "鍥剧墖鎹曡幏",
            "visual": [
                "鎸?PrintScreen 鎴浘",
                "娴獥鑷姩鍒锋柊锛屾埅鍥惧嚭鐜板湪椤堕儴",
                "鏄剧ず缂╃暐鍥鹃瑙?,
                "鐐瑰嚮鏉＄洰鐩存帴绮樿创鍥剧墖"
            ],
            "subtitle": "鎴浘涔熻兘鑷姩淇濆瓨 | 缂╃暐鍥句竴鐩簡鐒?| 鐐瑰嚮鐩存帴绮樿创",
            "narration": "",
            "bgm_beat": "鍒囩墖"
        })

        # ---- 鏍稿績鍗栫偣4锛氭敹钘忎笌绮樿创锛?2-38绉掞級----
        self.scenes.append({
            "timestamp": "0:32-0:38",
            "duration": "6s",
            "title": "鏀惰棌涓庣矘璐?,
            "visual": [
                "鐐瑰嚮 猸愶笍 鏀惰棌甯哥敤鎻愮ず璇?,
                "鍒囨崲鍒?1鏀惰棌 鏍囩鏌ョ湅",
                "鐐瑰嚮浠绘剰鏉＄洰",
                "鍒囨崲鍒扮紪杈戝櫒锛屽唴瀹硅嚜鍔ㄧ矘璐村埌鍏夋爣澶?
            ],
            "subtitle": "猸愶笍 鏀惰棌甯哥敤鍐呭 | 鐐瑰嚮鍗崇矘璐?| 涓嶉渶瑕佸啀澶嶅埗",
            "narration": "",
            "bgm_beat": "鍒囩墖"
        })

        # ---- 鏍稿績鍗栫偣5锛氱紦瀛樼鐞嗭紙38-44绉掞級----
        self.scenes.append({
            "timestamp": "0:38-0:44",
            "duration": "6s",
            "title": "缂撳瓨绠＄悊",
            "visual": [
                "鐐瑰嚮'娓呯悊'鎸夐挳锛屾墦寮€娓呯悊绐楀彛",
                "椤堕儴鏄剧ず: '缂撳瓨鍗犵敤: 15.6 MB'",
                "鍕鹃€夊鏉¤褰曟壒閲忓垹闄?,
                "宸插垹闄や繚鐣?澶╄嚜鍔ㄦ竻鐞?
            ],
            "subtitle": "缂撳瓨澶у皬涓€鐩簡鐒?| 鎵归噺娓呯悊 | 7澶╄嚜鍔ㄥ洖鏀?,
            "narration": "",
            "bgm_beat": "鍒囩墖"
        })

        # ---- 缁撳熬 CTA锛?4-50绉掞級----
        self.scenes.append({
            "timestamp": "0:44-0:50",
            "duration": "6s",
            "title": "缁撳熬CTA",
            "visual": [
                "娴獥鍏抽棴锛屽洖鍒版闈?,
                "鎵樼洏鍥炬爣钃濊壊鍦嗗舰闂儊",
                "澶у瓧寮瑰叆: 'Ctrl+Shift+V 寮€濮嬩綋楠?",
                "璇濋鏍囩寮瑰嚭: #vibecoding澶ц祻"
            ],
            "subtitle": "瀹屽叏鏈湴杩愯 | 淇濇姢闅愮 | Ctrl+Shift+V 寮€濮嬩綋楠?,
            "narration": "",
            "bgm_beat": "drop 鏀跺熬"
        })

    def print_script(self):
        print("=" * 70)
        print("  鍓创鏉垮蹇樺綍 鈥?鐭棰戝綍灞忚剼鏈?)
        print("  璇濋: #vibecoding澶ц祻")
        print("  骞冲彴: 鎶栭煶 / B绔?/ 灏忕孩涔?)
        print("  寤鸿鏃堕暱: 45-50 绉?)
        print("=" * 70)

        total = 0
        for scene in self.scenes:
            dur = int(scene["duration"].replace("s", ""))
            total += dur
            print(f"\n銆恵scene['timestamp']} | {scene['duration']}銆憑scene['title']}")
            print("-" * 50)
            print("鐢婚潰:")
            for v in scene["visual"]:
                print(f"  鈻?{v}")
            print(f"瀛楀箷: {scene['subtitle']}")
            print(f"BGM鑺傚: {scene['bgm_beat']}")

        print(f"\n{'='*70}")
        print(f"鎬绘椂闀? {total} 绉?)
        print(f"{'='*70}")

        print("\n" + "=" * 70)
        print("鍓緫寤鸿:")
        print("=" * 70)
        print("""
1. 鍓?绉掑繀椤绘姄浣忔敞鎰忓姏锛岀敤澶у瓧+寮瑰叆鍔ㄧ敾
2. 姣?绉掍竴涓妭濂忕偣锛岄厤鍚圔GM鐨刣rop/鍒囩墖
3. 鎿嶄綔褰曞睆鐢?.2-1.5鍊嶉€熸挱鏀撅紝澧炲姞鑺傚鎰?4. 鍏抽敭鎿嶄綔锛堟寜鏁板瓧閿€佹敹钘忥級鐢ㄦ斁澶х壒鏁?闊虫晥
5. 馃摉 鍜?猸愶笍 鏍囪瘑鍙樹寒鏃剁敤闂厜鐗规晥
6. 缁撳熬鎵樼洏鍥炬爣闂儊寮曞鐢ㄦ埛灏濊瘯
7. 瀛楀箷鐢ㄧ櫧鑹茬矖浣擄紝鍏抽敭璇嶇敤 accent 鑹?#7eb8ff 楂樹寒
8. 娣诲姞鎵撳瓧鏈洪煶鏁堥厤鍚堟搷浣?""")

        print("=" * 70)
        print("瀹屾暣瀛楀箷绋匡紙鍙洿鎺ュ鍒跺埌鍓緫杞欢锛?")
        print("=" * 70)
        for scene in self.scenes:
            print(f"\n[{scene['timestamp']}] {scene['subtitle']}")


if __name__ == "__main__":
    script = ShortVideoScript()
    script.print_script()
