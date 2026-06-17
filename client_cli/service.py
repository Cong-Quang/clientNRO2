import cmd as C
from network import Message, NRoSession


class Service:
    def __init__(self, session: NRoSession):
        self.session = session

    def _send(self, msg: Message):
        if self.session:
            self.session.sendMessage(msg)
        msg.cleanup()

    def messageNotLogin(self, command: int) -> Message:
        msg = Message(C.CMD_NOT_LOGIN)
        msg.writeByte(command)
        return msg

    def messageNotMap(self, command: int) -> Message:
        msg = Message(C.CMD_NOT_MAP)
        msg.writeByte(command)
        return msg

    def messageSubCommand(self, command: int) -> Message:
        msg = Message(C.CMD_SUB_COMMAND)
        msg.writeByte(command)
        return msg

    def setClientType(self):
        msg = self.messageNotLogin(C.CMD_CLIENT_INFO)
        msg.writeByte(1)
        msg.writeByte(1)
        msg.writeBoolean(False)
        msg.writeInt(320)
        msg.writeInt(240)
        msg.writeBoolean(False)
        msg.writeBoolean(False)
        msg.writeUTF(f"Windows|{self._get_version()}")
        msg.writeShort(0)
        self._send(msg)

    def _get_version(self) -> str:
        return "1.0.0"

    def login(self, username: str, password: str, version: str = "1.0.0", type_: int = 0):
        msg = self.messageNotLogin(C.CMD_LOGIN)
        msg.writeUTF(username)
        msg.writeUTF(password)
        msg.writeUTF(version)
        msg.writeByte(type_)
        self._send(msg)

    def selectChar(self, charname: str):
        msg = Message(C.CMD_NOT_MAP)
        msg.writeByte(C.CMD_SELECT_PLAYER)
        msg.writeUTF(charname)
        self._send(msg)

    def createChar(self, name: str, gender: int, hair: int):
        msg = Message(C.CMD_NOT_MAP)
        msg.writeByte(C.CMD_CREATE_PLAYER)
        msg.writeUTF(name)
        msg.writeByte(gender)
        msg.writeByte(hair)
        self._send(msg)

    def requestChangeMap(self):
        msg = Message(C.CMD_MAP_CHANGE)
        self._send(msg)

    def requestChangeZone(self, zoneId: int):
        msg = Message(C.CMD_ZONE_CHANGE)
        msg.writeByte(zoneId)
        self._send(msg)

    def charMove(self, cx: int, cy: int, cdir: int):
        msg = Message(C.CMD_PLAYER_MOVE)
        msg.writeByte(0)
        msg.writeShort(cx)
        msg.writeShort(cy)
        self._send(msg)

    def chat(self, text: str):
        msg = Message(C.CMD_CHAT_MAP)
        msg.writeUTF(text)
        self._send(msg)

    def chatPlayer(self, text: str, playerId: int):
        msg = Message(-72 & 0xFF)
        msg.writeInt(playerId)
        msg.writeUTF(text)
        self._send(msg)

    def chatGlobal(self, text: str):
        msg = Message(-71 & 0xFF)
        msg.writeUTF(text)
        self._send(msg)

    def chatPrivate(self, to: str, text: str):
        msg = Message(91)
        msg.writeUTF(to)
        msg.writeUTF(text)
        self._send(msg)

    def openMenu(self, npcId: int):
        msg = Message(C.CMD_OPEN_UI_MENU)
        msg.writeShort(npcId)
        self._send(msg)

    def menu(self, npcId: int, menuId: int, optionId: int):
        msg = Message(C.CMD_MENU)
        msg.writeByte(npcId)
        msg.writeByte(menuId)
        msg.writeByte(optionId)
        self._send(msg)

    def confirmMenu(self, npcID: int, select: int):
        msg = Message(C.CMD_OPEN_UI_CONFIRM)
        msg.writeShort(npcID)
        msg.writeByte(select)
        self._send(msg)

    def pickItem(self, itemMapId: int):
        msg = Message(C.CMD_ITEMMAP_MYPICK)
        msg.writeShort(itemMapId)
        self._send(msg)

    def throwItem(self, index: int):
        msg = Message(C.CMD_ME_THROW)
        msg.writeByte(index)
        self._send(msg)

    def useItem(self, type_: int, where: int, index: int, template: int = -1):
        msg = Message(C.CMD_USE_ITEM)
        msg.writeByte(type_)
        msg.writeByte(where)
        msg.writeByte(index)
        if index == -1:
            msg.writeShort(template)
        self._send(msg)

    def buyItem(self, type_: int, id_: int, quantity: int = 1):
        msg = Message(C.CMD_ITEM_BUY)
        msg.writeByte(type_)
        msg.writeShort(id_)
        if quantity > 1:
            msg.writeShort(quantity)
        self._send(msg)

    def saleItem(self, action: int, type_: int, id_: int):
        msg = Message(C.CMD_ITEM_SALE)
        msg.writeByte(action)
        msg.writeByte(type_)
        msg.writeShort(id_)
        self._send(msg)

    def selectSkill(self, skillTemplateId: int):
        msg = Message(C.CMD_SKILL_SELECT)
        msg.writeShort(skillTemplateId)
        self._send(msg)

    def upSkill(self, skillTemplateId: int, point: int):
        msg = self.messageSubCommand(C.SUB_SKILL_UP)
        msg.writeShort(skillTemplateId)
        msg.writeByte(point)
        self._send(msg)

    def upPotential(self, typePotential: int, num: int):
        msg = self.messageSubCommand(C.SUB_POTENTIAL_UP)
        msg.writeByte(typePotential)
        msg.writeShort(num)
        self._send(msg)

    def sendPlayerAttack(self, mobIds: list[int], charIds: list[int], type_: int, cdir: int):
        if type_ == 0:
            return
        if mobIds and charIds:
            if type_ == 1:
                msg = Message(C.CMD_PLAYER_ATTACK_N_P)
            elif type_ == 2:
                msg = Message(67)
            else:
                return
            msg.writeByte(len(mobIds))
            for mobId in mobIds:
                msg.writeByte(mobId)
            for charId in charIds:
                msg.writeInt(charId)
        elif mobIds:
            msg = Message(C.CMD_PLAYER_ATTACK_NPC)
            for mobId in mobIds:
                msg.writeByte(mobId)
        elif charIds:
            msg = Message(-60 & 0xFF)
            for charId in charIds:
                msg.writeInt(charId)
        else:
            return
        msg.writeSByte(cdir)
        self._send(msg)

    def skillNotFocus(self, status: int):
        msg = Message(C.CMD_SKILL_NOT_FOCUS)
        msg.writeByte(status)
        self._send(msg)

    def finishLoadMap(self):
        msg = Message(C.CMD_FINISH_LOADMAP)
        self._send(msg)

    def finishUpdate(self):
        msg = Message(C.CMD_FINISH_UPDATE)
        self._send(msg)

    def clientOk(self):
        msg = self.messageNotMap(C.CMD_CLIENT_OK)
        self._send(msg)

    def requestItem(self, typeUI: int):
        msg = self.messageSubCommand(C.SUB_REQUEST_ITEM)
        msg.writeByte(typeUI)
        self._send(msg)

    def requestItemInfo(self, typeUI: int, indexUI: int):
        msg = Message(C.CMD_REQUEST_ITEM_INFO)
        msg.writeByte(typeUI)
        msg.writeByte(indexUI)
        self._send(msg)

    def getItem(self, type_: int, id_: int):
        msg = Message(C.CMD_GET_ITEM)
        msg.writeByte(type_)
        msg.writeByte(id_)
        self._send(msg)

    def getBody(self, action: int):
        msg = Message(C.CMD_BODY)
        msg.writeByte(action)
        self._send(msg)

    def getBag(self, action: int):
        msg = Message(C.CMD_BAG)
        msg.writeByte(action)
        self._send(msg)

    def getChest(self, action: int):
        msg = Message(C.CMD_BOX)
        msg.writeByte(action)
        self._send(msg)

    def openUIZone(self):
        msg = Message(C.CMD_OPEN_UI_ZONE)
        self._send(msg)

    def updateMap(self):
        msg = self.messageNotMap(C.CMD_UPDATE_MAP)
        self._send(msg)

    def updateSkill(self):
        msg = self.messageNotMap(C.CMD_UPDATE_SKILL)
        self._send(msg)

    def updateItem(self):
        msg = self.messageNotMap(C.CMD_UPDATE_ITEM)
        self._send(msg)

    def updateData(self):
        msg = Message(C.CMD_UPDATE_DATA)
        self._send(msg)

    def sendCheckController(self):
        msg = Message(C.CMD_CHECK_CONTROLLER)
        self._send(msg)

    def sendCheckMap(self):
        msg = Message(C.CMD_CHECK_MAP)
        self._send(msg)

    def gotoPlayer(self, playerId: int):
        msg = Message(18)
        msg.writeInt(playerId)
        self._send(msg)

    def getTask(self, npcTemplateId: int, menuId: int, optionId: int = -1):
        msg = Message(C.CMD_TASK_GET)
        msg.writeByte(npcTemplateId)
        msg.writeByte(menuId)
        if optionId >= 0:
            msg.writeByte(optionId)
        self._send(msg)

    def addFriend(self, name: str):
        msg = Message(53)
        msg.writeUTF(name)
        self._send(msg)

    def returnTownFromDead(self):
        msg = Message(C.CMD_ME_BACK)
        self._send(msg)

    def wakeUpFromDead(self):
        msg = Message(C.CMD_ME_LIVE)
        self._send(msg)

    def magicTree(self, type_: int):
        msg = Message(C.CMD_MAGIC_TREE)
        msg.writeByte(type_)
        self._send(msg)

    def petInfo(self):
        msg = Message(C.CMD_PET_INFO)
        self._send(msg)

    def petStatus(self, status: int):
        msg = Message(C.CMD_PET_STATUS)
        msg.writeByte(status)
        self._send(msg)

    def transportNow(self):
        msg = Message(C.CMD_TRANSPORT)
        self._send(msg)

    def getFlag(self, action: int, flagType: int = 0):
        msg = Message(C.CMD_CHANGE_FLAG)
        msg.writeByte(action)
        if action != 0:
            msg.writeByte(flagType)
        self._send(msg)

    def setLockInventory(self, pass_: int):
        msg = Message(C.CMD_LOCK_INVENTORY)
        msg.writeInt(pass_)
        self._send(msg)

    def requestSkill(self, skillId: int):
        msg = self.messageNotMap(C.CMD_REQUEST_SKILL)
        msg.writeShort(skillId)
        self._send(msg)

    def requestMaptemplate(self, maptemplateId: int):
        msg = self.messageNotMap(C.CMD_REQUEST_MAPTEMPLATE)
        msg.writeByte(maptemplateId)
        self._send(msg)

    def requestModTemplate(self, modTemplateId: int):
        msg = Message(C.CMD_REQUEST_MOB_TEMPLATE)
        msg.writeShort(modTemplateId)
        self._send(msg)

    def sendClientInput(self, inputs: list[str]):
        msg = Message(C.CMD_CLIENT_INPUT)
        msg.writeByte(len(inputs))
        for t in inputs:
            msg.writeUTF(t)
        self._send(msg)

    def friend(self, action: int, playerId: int = -1):
        msg = Message(C.CMD_FRIEND)
        msg.writeByte(action)
        if playerId != -1:
            msg.writeInt(playerId)
        self._send(msg)

    def getPlayerMenu(self, playerID: int):
        msg = Message(C.CMD_PLAYER_MENU)
        msg.writeInt(playerID)
        self._send(msg)

    def getEffData(self, id_: int):
        msg = Message(C.CMD_GET_EFFDATA if hasattr(C, 'CMD_GET_EFFDATA') else -66 & 0xFF)
        msg.writeShort(id_)
        self._send(msg)
