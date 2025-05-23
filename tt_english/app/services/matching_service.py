# app/services/matching_service.py
from datetime import date
from typing import List, Tuple, Optional
from sqlmodel import Session
import random

from app.db.models.user_model import User
from app.db.models.chat_room_model import ChatRoom # 需要导入 ChatRoom
from app.crud import event_signup_crud, match_crud

class MatchingService:
    def __init__(self, db: Session):
        self.db = db

    def _get_eligible_users(self, event_date: date) -> List[User]:
        signed_up_users = event_signup_crud.get_all_active_users_signed_up_for_date(
            self.db, event_date=event_date
        )
        eligible_users = [user for user in signed_up_users if user.english_level is not None]
        random.shuffle(eligible_users) # 初始打乱，增加一些随机性
        return eligible_users

    def perform_matching(self, event_date: date) -> int:
        if match_crud.check_if_matches_generated_for_date(self.db, event_date):
            print(f"警告: {event_date} 的匹配已经生成过。")
            # 可以根据需要决定是否清除或直接返回
            # match_crud.delete_matches_for_date(self.db, event_date) # 如果需要重新生成则取消注释
            # print(f"{event_date} 的旧匹配已清除。")
            return 0 # 或者抛出异常表明已匹配

        users_to_match = self._get_eligible_users(event_date)

        if not users_to_match or len(users_to_match) < 2:
            print(f"{event_date}: 没有足够的用户进行匹配 (需要至少2人)。实际人数: {len(users_to_match)}")
            return 0

        # 1. 按英语水平排序 (值越小水平越初级，便于寻找相近水平)
        users_to_match.sort(key=lambda u: u.english_level)
        print(f"{event_date}: 参与匹配用户数 {len(users_to_match)}, 水平排序后: {[ (u.id, u.english_level) for u in users_to_match]}")

        created_rooms_count = 0
        # 用于存储已创建的二人房间及其代表性英语水平 (例如房间内两人的平均水平，或其中一人的水平)
        # (room_db_object, representative_level)
        two_person_rooms_created: List[Tuple[ChatRoom, float]] = []
        
        participants_buffer = list(users_to_match)

        # 2. 优先进行一对一匹配 (两人房)
        # 我们将从头开始，每次尝试取两个水平相近的人
        # 设定一个最大可接受的英语水平差异阈值（可选，但推荐）
        MAX_LEVEL_DIFFERENCE = 1 # 例如，只允许水平相同或差异为1的用户匹配

        # 使用一个索引来遍历，因为我们会从中移除元素
        i = 0
        while i < len(participants_buffer) -1: # 至少需要两个人才能匹配
            user1 = participants_buffer[i]
            
            # 寻找与 user1 水平相近的 user2
            # 最简单的方式是取下一个 user2 = participants_buffer[i+1]
            # 但为了更好的水平控制，我们可以向前查找几个用户
            best_match_user2 = None
            smallest_diff = float('inf')
            best_match_idx = -1

            # 在 user1 后面的用户中寻找最佳匹配 (在设定的差异阈值内)
            # 查找范围可以限定，比如 user1 后面的 k 个用户
            # 为了简化，我们先考虑直接取下一个 (i+1)，如果差异在阈值内
            if abs(user1.english_level - participants_buffer[i+1].english_level) <= MAX_LEVEL_DIFFERENCE:
                best_match_user2 = participants_buffer[i+1]
                best_match_idx = i + 1
            
            if best_match_user2:
                room_participants = [user1, best_match_user2]
                
                # 从 participants_buffer 中移除已匹配的用户
                # 必须先移除索引较大的，再移除索引较小的，避免索引错位
                participants_buffer.pop(best_match_idx)
                participants_buffer.pop(i)
                
                # 创建二人聊天室
                new_room = match_crud.create_chat_room(self.db, event_date=event_date, room_type="2-person")
                created_rooms_count += 1
                avg_level = (user1.english_level + best_match_user2.english_level) / 2.0
                two_person_rooms_created.append((new_room, avg_level))

                print(f"创建二人房间: {new_room.room_identifier}, 用户: [({user1.id},{user1.english_level}), ({best_match_user2.id},{best_match_user2.english_level})], 平均水平: {avg_level}")
                for p_user in room_participants:
                    match_crud.add_participant_to_room(self.db, room_id=new_room.id, user_id=p_user.id)
                
                # 因为移除了元素，所以下一次循环的i不需要增加 (i保持不变，检查新的participants_buffer[i])
            else:
                # 如果 user1 找不到合适的匹配 (例如，下一个用户的水平差异过大)
                # 这种情况下，user1 暂时会被跳过，i 增加，尝试为下一个用户匹配
                # 这个被跳过的 user1 可能会成为最后的落单者
                i += 1
        
        # 3. 处理剩余的用户 (此时 participants_buffer 中剩下的都是无法两两配对的)
        if len(participants_buffer) == 1 and two_person_rooms_created:
            lone_user = participants_buffer[0]
            print(f"处理落单用户: ({lone_user.id}, {lone_user.english_level})")

            # 为这个落单用户寻找一个最合适的二人房间加入
            best_room_to_join: Optional[ChatRoom] = None
            min_level_diff_to_room = float('inf')

            for room, room_avg_level in two_person_rooms_created:
                # 计算落单用户与该房间代表水平的差异
                # 同时，我们也应该考虑落单用户与房间内已有成员的个体差异，确保不会太离谱
                # 这里简化为与房间平均水平的差异
                diff = abs(lone_user.english_level - room_avg_level)
                
                # 检查与房间内每个成员的差异是否也在可接受范围内 (可选，更严格)
                # room_original_participants = match_crud.get_participants_for_room(self.db, room.id)
                # individual_diffs_ok = True
                # for p in room_original_participants:
                #     if abs(lone_user.english_level - p.english_level) > MAX_LEVEL_DIFFERENCE + 1: # 可以用更宽松的阈值
                #         individual_diffs_ok = False
                #         break
                # if not individual_diffs_ok:
                #     continue

                if diff < min_level_diff_to_room:
                    # 同时，要确保加入后，这个三人间的水平差异不会过大
                    # 这里可以加入更多关于“水平相近”的判断逻辑
                    min_level_diff_to_room = diff
                    best_room_to_join = room
            
            if best_room_to_join:
                print(f"落单用户 {lone_user.id} 将加入房间 {best_room_to_join.room_identifier}")
                match_crud.add_participant_to_room(self.db, room_id=best_room_to_join.id, user_id=lone_user.id)
                
                # 更新房间类型为三人房
                best_room_to_join.room_type = "3-person"
                self.db.add(best_room_to_join)
                self.db.commit()
                self.db.refresh(best_room_to_join)
                
                participants_buffer.pop(0) # 从buffer移除已处理的落单用户
            else:
                print(f"落单用户 {lone_user.id} 未能找到合适的二人房间加入 (可能所有房间水平差异过大)。该用户轮空。")

        elif participants_buffer: # 如果还剩下超过1个用户，说明之前的两两配对逻辑有缺陷，或者人数太少
            print(f"匹配结束后仍有多个用户未处理: {[ (u.id, u.english_level) for u in participants_buffer]} (可能轮空)")
        
        if not participants_buffer:
            print("所有用户均已成功匹配或处理。")

        return created_rooms_count # 注意：这个计数目前只统计了初始创建的房间数，三人房是修改的