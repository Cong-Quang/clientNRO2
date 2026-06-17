import threading
from network import Message, NRoSession
from service import Service
from handler import MessageHandler
from state import GameState
from logger import log
from handlers import (
    ConnectionHandler,
    AuthHandler,
    WorldHandler,
    CommunicationHandler,
    InteractionHandler,
    SocialHandler,
)
import cmd as C


class GameClient(MessageHandler):
    def __init__(self, host='127.0.0.1', port=14445):
        self.state = GameState()
        self.session = NRoSession(host, port)
        self.session.setHandler(self)
        self.service = Service(self.session)

        self.connection_handler = ConnectionHandler(self.state, self.service)
        self.auth_handler = AuthHandler(self.state, self.service)
        self.world_handler = WorldHandler(self.state, self.service)
        self.communication_handler = CommunicationHandler(self.state)
        self.interaction_handler = InteractionHandler(self.state)
        self.social_handler = SocialHandler(self.state)

        self._dispatcher = self._build_dispatcher()

    def _build_dispatcher(self):
        return {
            C.CMD_LOGIN: self.auth_handler.handle_char_list,
            12: self.social_handler.handle_extra_big,
            24: self.social_handler.handle_extra,
            C.CMD_REGISTER: self.social_handler.handle_register,
            C.CMD_CLIENT_INFO: self.social_handler.handle_client_info,
            C.CMD_DELETE_PLAYER: self.social_handler.handle_delete_player,
            6: self.world_handler.handle_send_money,
            C.CMD_UPDATE_SKILL: self.auth_handler.handle_not_login,
            C.CMD_UPDATE_ITEM: self.auth_handler.handle_not_login,
            C.CMD_REQUEST_SKILL: self.auth_handler.handle_not_login,
            C.CMD_REQUEST_MAPTEMPLATE: self.auth_handler.handle_not_login,
            C.CMD_REQUEST_MOB_TEMPLATE: self.auth_handler.handle_not_login,
            C.CMD_CLIENT_OK: self.social_handler.handle_client_ok,
            C.CMD_CLIENT_OK_INMAP: self.social_handler.handle_client_ok_inmap,
            C.CMD_UPDATE_VERSION_OK: self.social_handler.handle_update_version_ok,
            C.CMD_CHANGE_NAME: self.social_handler.handle_change_name,
            C.CMD_OPEN_UI_ZONE: self.interaction_handler.handle_open_ui_zone,
            C.CMD_OPEN_UI_PT: self.interaction_handler.handle_open_ui_pt,
            C.CMD_OPEN_UI_SHOP: self.interaction_handler.handle_open_ui_shop,
            C.CMD_OPEN_UI_COLLECT: self.interaction_handler.handle_open_ui_collect,
            C.CMD_OPEN_UI_TRADE: self.interaction_handler.handle_open_ui_trade,
            C.CMD_OPEN_UI_SAY: self.interaction_handler.handle_open_ui_say,
            C.CMD_NPC_MISS: self.interaction_handler.handle_npc_miss,
            C.CMD_RESET_POINT: self.world_handler.handle_reset_point,
            C.CMD_ALERT_MESSAGE: self.communication_handler.handle_alert_message,
            C.CMD_AUTO_SERVER: self.social_handler.handle_auto_server,
            C.CMD_TRADE_INVITE_CANCEL: self.social_handler.handle_trade_invite_cancel,
            C.CMD_BOSS_SKILL: self.communication_handler.handle_boss_skill,
            C.CMD_MABU_HOLD: self.communication_handler.handle_mabu_hold,
            C.CMD_FRIEND_INVITE: self.social_handler.handle_friend_invite,
            C.CMD_PLAYER_ATTACK_NPC: self.world_handler.handle_player_attack_n_p,
            C.CMD_HAVE_ATTACK_PLAYER: self.communication_handler.handle_have_attack_player,
            C.CMD_MOVE_FAST: self.world_handler.handle_move_fast,
            C.CMD_PARTY_INVITE: self.social_handler.handle_party_invite,
            C.CMD_PARTY_ACCEPT: self.social_handler.handle_party_accept,
            C.CMD_PARTY_CANCEL: self.social_handler.handle_party_cancel,
            C.CMD_PLAYER_IN_PARTY: self.social_handler.handle_player_in_party,
            C.CMD_PARTY_OUT: self.social_handler.handle_party_out,
            C.CMD_FRIEND_ADD: self.social_handler.handle_friend_add,
            C.CMD_NPC_CHAT: self.communication_handler.handle_npc_chat,
            C.CMD_FUSION: self.social_handler.handle_fusion,
            C.CMD_SET_POS: self.world_handler.handle_set_pos,
            C.CMD_ANDROID_PACK: self.social_handler.handle_android_pack,
            C.CMD_RADA_CARD: self.social_handler.handle_rada_card,
            C.CMD_CHAR_EFFECT: self.social_handler.handle_char_effect,
            C.CMD_LUCKY_ROUND: self.social_handler.handle_lucky_round,
            C.CMD_QUAYSO: self.social_handler.handle_quayso,
            C.CMD_CLIENT_INPUT: self.social_handler.handle_client_input,
            C.CMD_CHECK_CONTROLLER: self.social_handler.handle_check_controller,
            C.CMD_CHECK_MAP: self.social_handler.handle_check_map,
            C.CMD_SET_CLIENTTYPE: self.social_handler.handle_set_clienttype,
            C.CMD_MAP_TRASPORT: self.social_handler.handle_map_transport,
            C.CMD_UPDATE_BODY: self.world_handler.handle_update_body,
            C.CMD_SERVERSCREEN: self.social_handler.handle_server_screen,
            C.CMD_UPDATE_DATA: self.social_handler.handle_update_data,
            C.CMD_TILE_SET: self.social_handler.handle_tile_set,
            C.CMD_CHECK_MOVE: self.world_handler.handle_check_move,
            C.CMD_GIAO_DICH: self.social_handler.handle_giao_dich,
            C.CMD_COMBINNE: self.social_handler.handle_combine,
            C.CMD_FRIEND: self.social_handler.handle_friend,
            C.CMD_PLAYER_MENU: self.social_handler.handle_player_menu,
            C.CMD_PET_INFO: self.social_handler.handle_pet_info,
            C.CMD_PET_STATUS: self.social_handler.handle_pet_status,
            C.CMD_ITEM_TIME: self.social_handler.handle_item_time,
            C.CMD_TRANSPORT: self.social_handler.handle_transport,
            C.CMD_CHANGE_FLAG: self.social_handler.handle_flag,
            C.CMD_LOCK_INVENTORY: self.social_handler.handle_lock_inventory,
            C.CMD_MAGIC_TREE: self.interaction_handler.handle_magic_tree,
            C.CMD_BIG_MESSAGE: self.communication_handler.handle_big_msg,
            C.CMD_CLAN_CREATE_INFO: self.social_handler.handle_clan_create,
            C.CMD_SPEACIAL_SKILL: self.interaction_handler.handle_special_skill,
            C.CMD_SERVER_EFFECT: self.social_handler.handle_server_effect,
            C.CMD_BIG_BOSS: self.social_handler.handle_big_boss,
            C.CMD_BIG_BOSS_2: self.social_handler.handle_big_boss_2,
            C.CMD_PLEASE_INPUT_PARTY: self.social_handler.handle_please_input_party,
            C.CMD_ACCEPT_PLEASE_PARTY: self.social_handler.handle_accept_please_party,
            C.CMD_REQUEST_PLAYERS: self.social_handler.handle_request_players,
            C.CMD_UPDATE_ACHIEVEMENT: self.social_handler.handle_update_achievement,
            C.CMD_TRADE_INVITE: self.social_handler.handle_trade_invite,
            C.CMD_TRADE_INVITE_ACCEPT: self.social_handler.handle_trade_invite_accept,
            C.CMD_TRADE_LOCK_ITEM: self.social_handler.handle_trade_lock_item,
            C.CMD_TRADE_ACCEPT: self.social_handler.handle_trade_accept,
            C.CMD_ITEM_BUY: self.interaction_handler.handle_shop,
            C.CMD_ITEM_SALE: self.interaction_handler.handle_shop,
            C.CMD_UPGRADE: self.interaction_handler.handle_upgrade,
            C.CMD_MENU: self.interaction_handler.handle_menu,
            C.CMD_OPEN_UI: self.interaction_handler.handle_npc_menu,
            C.CMD_OPEN_MENU_ID: self.interaction_handler.handle_menu_id,
            C.CMD_OPEN_UI_CONFIRM: self.interaction_handler.handle_confirm,
            C.CMD_OPEN_UI_MENU: self.interaction_handler.handle_npc_menu,
            C.CMD_SKILL_SELECT: self.interaction_handler.handle_skill_select,
            C.CMD_REQUEST_ITEM_INFO: self.interaction_handler.handle_item_info,
            C.CMD_TASK_GET: self.interaction_handler.handle_task,
            C.CMD_CHAT_MAP: self.communication_handler.handle_chat,
            C.CMD_PLAYER_ADD: self.world_handler.handle_player_add,
            C.CMD_PLAYER_REMOVE: self.world_handler.handle_player_remove,
            C.CMD_PLAYER_MOVE: self.world_handler.handle_player_move,
            C.CMD_PLAYER_DIE: self.world_handler.handle_player_die,
            C.CMD_PLAYER_UP_EXP: self.world_handler.handle_player_exp,
            C.CMD_ME_CHANGE_COIN: self.world_handler.handle_me_change_coin,
            C.CMD_ME_DIE: self.world_handler.handle_me_die,
            C.CMD_ME_LIVE: self.world_handler.handle_me_live,
            C.CMD_ME_BACK: self.world_handler.handle_me_back,
            C.CMD_PLAYER_THROW: self.world_handler.handle_player_throw,
            C.CMD_MOB_HP: self.world_handler.handle_mob_hp,
            C.CMD_NOT_LOGIN: self.auth_handler.handle_not_login,
            C.CMD_NOT_MAP: self.auth_handler.handle_not_map,
            C.CMD_SUB_COMMAND: self.world_handler.handle_sub_command,
            C.CMD_DIALOG_MESSAGE: self.communication_handler.handle_dialog,
            C.CMD_SERVER_MESSAGE: self.communication_handler.handle_server_msg,
            C.CMD_MAP_INFO: self.world_handler.handle_map_info,
            C.CMD_MAP_CHANGE: self.world_handler.handle_map_change,
            C.CMD_MAP_CLEAR: self.world_handler.handle_map_clear,
            C.CMD_ITEMMAP_MYPICK: self.world_handler.handle_itemmap_mypick,
            C.CMD_ME_THROW: self.world_handler.handle_me_throw,
            C.CMD_ME_LOAD_POINT: self.world_handler.handle_me_load_point,
            C.CMD_USE_ITEM: self.interaction_handler.handle_use_item,
            C.CMD_SHOP: self.interaction_handler.handle_shop,
            C.CMD_SKILL_NOT_FOCUS: self.interaction_handler.handle_skill_not_focus,
            C.CMD_GET_ITEM: self.interaction_handler.handle_get_item,
            C.CMD_FINISH_LOADMAP: self.world_handler.handle_finish_loadmap,
            C.CMD_FINISH_UPDATE: self.world_handler.handle_finish_update,
            C.CMD_BODY: self.interaction_handler.handle_body,
            C.CMD_BAG: self.interaction_handler.handle_bag,
            C.CMD_BOX: self.interaction_handler.handle_box,
            C.CMD_ZONE_CHANGE: self.world_handler.handle_map_change,
            C.CMD_PLAYER_ATTACK_N_P: self.world_handler.handle_player_attack_n_p,
            C.CMD_GET_SESSION_ID: self.auth_handler.handle_not_login,
            182: self.auth_handler.handle_get_image_source,
        }

    def onConnectOK(self, isMain: bool):
        self.connection_handler.on_connect_ok(isMain)

    def onConnectionFail(self, isMain: bool):
        self.connection_handler.on_connection_fail(isMain)

    def onDisconnected(self, isMain: bool):
        self.connection_handler.on_disconnected(isMain)

    def onMessage(self, msg: Message):
        cmd = msg.command
        handler = self._dispatcher.get(cmd)
        if handler:
            try:
                handler(msg)
            except Exception as e:
                log.error("NETWORK", f"cmd={cmd}: {e}")
        else:
            log.debug("NETWORK", f"cmd={cmd} size={msg.available()}")
