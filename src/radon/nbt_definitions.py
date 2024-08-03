# THIS IS IN PROGRESS #

from .utils import CplDefObject as obj, STRING_TYPE, INT_TYPE, CplDefArray as arr, FLOAT_TYPE

STRING_ARRAY_TYPE = arr(STRING_TYPE)
INT_ARRAY_TYPE = arr(INT_TYPE)
FLOAT_ARRAY_TYPE = arr(FLOAT_TYPE)
UUID_TYPE = INT_ARRAY_TYPE

ENTITIES_OBJ = obj({})
BLOCKS_Properties = obj({})  # TODO: this

ITEMS__Tag = obj({"Damage": INT_TYPE})  # Not finished
ITEMS__Attribute = obj(
    {"AttributeName": STRING_TYPE, "Amount": FLOAT_TYPE, "Slot": STRING_TYPE, "Operation": INT_TYPE,
     "UUID": UUID_TYPE})
ITEMS__FireworkExplosion = obj(
    {"Colors": INT_ARRAY_TYPE, "FadeColors": INT_ARRAY_TYPE, "Flicker": INT_TYPE, "Trail": INT_TYPE, "Type": INT_TYPE})
ENTITIES__ActiveEffect = obj(
    {"id": STRING_TYPE, "duration": INT_TYPE, "amplifier": INT_TYPE, "ambient": INT_TYPE, "show_particles": INT_TYPE,
     "show_icon": INT_TYPE})
ENTITIES__AttributeModifier = obj({"Name": STRING_TYPE, "Amount": FLOAT_TYPE, "Operation": INT_TYPE, "UUID": UUID_TYPE})
ENTITIES__Attribute = obj({"name": STRING_TYPE, "Base": FLOAT_TYPE, "Modifiers": arr(ENTITIES__AttributeModifier)})

ITEMS_Item = obj({"id": STRING_TYPE, "Count": INT_TYPE, "tag": ITEMS__Tag})
ITEMS_Enchantments = arr(obj({"id": STRING_TYPE, "lvl": INT_TYPE}))
ITEMS_StoredEnchantments = ITEMS_Enchantments
ITEMS_EntityTag = ENTITIES_OBJ
ITEMS_display = obj({"Name": STRING_TYPE, "Lore": STRING_ARRAY_TYPE, "color": INT_TYPE})
ITEMS_AttributeModifiers = arr(ITEMS__Attribute)
ITEMS_Unbreakable = INT_TYPE
ITEMS_SkullOwner = STRING_TYPE
ITEMS_HideFlags = INT_TYPE
ITEMS_CanDestroy = STRING_ARRAY_TYPE
ITEMS_PickupDelay = INT_TYPE
ITEMS_Age = INT_TYPE
ITEMS_generation = INT_TYPE
ITEMS_title = STRING_TYPE
ITEMS_author = STRING_TYPE
ITEMS_pages = STRING_TYPE
ITEMS_Fireworks = obj({"Explosions": arr(ITEMS__FireworkExplosion), "Flight": INT_TYPE})

# Only for blocks as items
ITEMS_CanPlaceOn = STRING_ARRAY_TYPE
ITEMS_BlockEntityTag = obj({})  # Not finished
ITEMS_BlockStateTag = obj({"facing": STRING_TYPE, "half": STRING_TYPE, "shape": STRING_TYPE})

# Entities
ENTITIES_UUID = UUID_TYPE
ENTITIES_Pos = INT_ARRAY_TYPE
ENTITIES_Inventory = arr(ITEMS_Item)
ENTITIES_SelectedItem = ITEMS_Item
ENTITIES_TileEntityData = ENTITIES_OBJ
ENTITIES_Motion = FLOAT_ARRAY_TYPE
ENTITIES_direction = FLOAT_ARRAY_TYPE
ENTITIES_power = FLOAT_ARRAY_TYPE
ENTITIES_ActiveEffects = arr(ENTITIES__ActiveEffect)
ENTITIES_rewardExp = INT_TYPE
ENTITIES_Passengers = arr(ENTITIES_OBJ)
ENTITIES_ArmorItems = arr(ITEMS_Item)
ENTITIES_HandItems = arr(ITEMS_Item)
ENTITIES_HandDropChances = FLOAT_ARRAY_TYPE
ENTITIES_ArmorDropChances = FLOAT_ARRAY_TYPE
ENTITIES_NoAI = INT_TYPE
ENTITIES_NoGravity = INT_TYPE
ENTITIES_Silent = INT_TYPE
ENTITIES_Fire = INT_TYPE
ENTITIES_Invulnerable = INT_TYPE
ENTITIES_Attributes = arr(ENTITIES__Attribute)
ENTITIES_Health = FLOAT_TYPE
ENTITIES_AngerTime = INT_TYPE
ENTITIES_AngryAt = UUID_TYPE
ENTITIES_CustomName = STRING_TYPE
ENTITIES_CustomNameVisible = INT_TYPE
ENTITIES_PersistenceRequired = INT_TYPE
ENTITIES_Type = INT_TYPE
ENTITIES_Saddle = INT_TYPE
ENTITIES_Tame = INT_TYPE
ENTITIES_Variant = INT_TYPE
ENTITIES_Size = INT_TYPE
ENTITIES_BlockState = obj({"Name": STRING_TYPE, "Properties": BLOCKS_Properties})
ENTITIES_Time = INT_TYPE
ENTITIES_DropItem = INT_TYPE
ENTITIES_id = STRING_TYPE
ENTITIES_fuse = INT_TYPE
ENTITIES_ExplosionPower = INT_TYPE
ENTITIES_ExplosionRadius = INT_TYPE
ENTITIES_powered = INT_TYPE
ENTITIES_AttachFace = INT_TYPE
ENTITIES_Peek = INT_TYPE
ENTITIES_APX = INT_TYPE
ENTITIES_APY = INT_TYPE
ENTITIES_APZ = INT_TYPE

# Villager
ENTITIES_Profession = INT_TYPE
ENTITIES_Offers = obj({"Recipes": arr(obj({"buy": ITEMS_Item, "maxUses": INT_TYPE, "sell": ITEMS_Item}))})

# Item Frame
ENTITIES_Facing = INT_TYPE
ENTITIES_ItemRotation = INT_TYPE
ENTITIES_Item = ITEMS_Item
ENTITIES_Invisible = INT_TYPE
ENTITIES_Fixed = INT_TYPE

# Potion
ENTITIES_Potion = STRING_TYPE
ENTITIES__CustomPotionEffect = obj({"Id": STRING_TYPE, "Amplifier": INT_TYPE, "Duration": INT_TYPE})
ENTITIES_CustomPotionEffects = ENTITIES_ActiveEffects
ENTITIES_CustomPotionColor = INT_TYPE

# Armor Stand
# ENTITIES_NoGravity: already defined
ENTITIES_ShowArms = INT_TYPE
ENTITIES_NoBasePlate = INT_TYPE
ENTITIES_Small = INT_TYPE
ENTITIES_Rotation = FLOAT_ARRAY_TYPE
ENTITIES_Marker = INT_TYPE
ENTITIES_Pose = obj(
    {"Head": FLOAT_ARRAY_TYPE, "Body": FLOAT_ARRAY_TYPE, "LeftArm": FLOAT_ARRAY_TYPE, "RightArm": FLOAT_ARRAY_TYPE,
     "LeftLeg": FLOAT_ARRAY_TYPE, "RightLeg": FLOAT_ARRAY_TYPE})
# ENTITIES_Invisible: already defined

# Turtle
ENTITIES_HomePosX = FLOAT_TYPE
ENTITIES_HomePosY = FLOAT_TYPE
ENTITIES_HomePosZ = FLOAT_TYPE
ENTITIES_TravelPosX = FLOAT_TYPE
ENTITIES_TravelPosY = FLOAT_TYPE
ENTITIES_TravelPosZ = FLOAT_TYPE
ENTITIES_HasEgg = INT_TYPE

# Assigning everything to one object type
ENTITIES_OBJ.content = {
    "Pos": ENTITIES_Pos,
    "UUID": ENTITIES_UUID,
    "Inventory": ENTITIES_Inventory,
    "SelectedItem": ENTITIES_SelectedItem,
    "TileEntityData": ENTITIES_TileEntityData,
    "Motion": ENTITIES_Motion,
    "direction": ENTITIES_direction,
    "power": ENTITIES_power,
    "ActiveEffects": ENTITIES_ActiveEffects,
    "rewardExp": ENTITIES_rewardExp,
    "Passengers": ENTITIES_Passengers,
    "ArmorItems": ENTITIES_ArmorItems,
    "HandItems": ENTITIES_HandItems,
    "HandDropChances": ENTITIES_HandDropChances,
    "ArmorDropChances": ENTITIES_ArmorDropChances,
    "NoAI": ENTITIES_NoAI,
    "NoGravity": ENTITIES_NoGravity,
    "Silent": ENTITIES_Silent,
    "Fire": ENTITIES_Fire,
    "Invulnerable": ENTITIES_Invulnerable,
    "Attributes": ENTITIES_Attributes,
    "Health": ENTITIES_Health,
    "AngerTime": ENTITIES_AngerTime,
    "AngryAt": ENTITIES_AngryAt,
    "CustomName": ENTITIES_CustomName,
    "CustomNameVisible": ENTITIES_CustomNameVisible,
    "PersistenceRequired": ENTITIES_PersistenceRequired,
    "Type": ENTITIES_Type,
    "Saddle": ENTITIES_Saddle,
    "Tame": ENTITIES_Tame,
    "Variant": ENTITIES_Variant,
    "Size": ENTITIES_Size,
    "BlockState": ENTITIES_BlockState,
    "Time": ENTITIES_Time,
    "DropItem": ENTITIES_DropItem,
    "id": ENTITIES_id,
    "fuse": ENTITIES_fuse,
    "ExplosionPower": ENTITIES_ExplosionPower,
    "ExplosionRadius": ENTITIES_ExplosionRadius,
    "powered": ENTITIES_powered,
    "AttachFace": ENTITIES_AttachFace,
    "Peek": ENTITIES_Peek,
    "APX": ENTITIES_APX,
    "APY": ENTITIES_APY,
    "APZ": ENTITIES_APZ,
    "Profession": ENTITIES_Profession,
    "Offers": ENTITIES_Offers,
    "Facing": ENTITIES_Facing,
    "ItemRotation": ENTITIES_ItemRotation,
    "Item": ENTITIES_Item,
    "Invisible": ENTITIES_Invisible,
    "Fixed": ENTITIES_Fixed,
    "Potion": ENTITIES_Potion,
    "CustomPotionEffects": ENTITIES_CustomPotionEffects,
    "CustomPotionColor": ENTITIES_CustomPotionColor,
    "ShowArms": ENTITIES_ShowArms,
    "NoBasePlate": ENTITIES_NoBasePlate,
    "Small": ENTITIES_Small,
    "Rotation": ENTITIES_Rotation,
    "Marker": ENTITIES_Marker,
    "Pose": ENTITIES_Pose,
    "HomePosX": ENTITIES_HomePosX,
    "HomePosY": ENTITIES_HomePosY,
    "HomePosZ": ENTITIES_HomePosZ,
    "TravelPosX": ENTITIES_TravelPosX,
    "TravelPosY": ENTITIES_TravelPosY,
    "TravelPosZ": ENTITIES_TravelPosZ,
    "HasEgg": ENTITIES_HasEgg
}

# Command Block
BLOCKS_Command = STRING_TYPE
BLOCKS_auto = INT_TYPE  # Needs redstone toggle

# Generic - Most of the tiles blocks
BLOCKS_CustomName = STRING_TYPE
BLOCKS_Lock = STRING_TYPE

# Beacon
BLOCKS_Primary = STRING_TYPE
BLOCKS_Secondary = STRING_TYPE
BLOCKS_Levels = INT_TYPE

# Entity Spawner
BLOCKS_EntityId = STRING_TYPE
BLOCKS_SpawnData = ENTITIES_OBJ
BLOCKS_SpawnCount = INT_TYPE
BLOCKS_SpawnRange = INT_TYPE
BLOCKS_RequiredPlayerRange = INT_TYPE
BLOCKS_Delay = INT_TYPE
BLOCKS_MinSpawnDelay = INT_TYPE
BLOCKS_MaxSpawnDelay = INT_TYPE
BLOCKS_MaxNearbyEntities = INT_TYPE
BLOCKS_SpawnPotentials = arr(obj({"data": ENTITIES_OBJ, "weight": INT_TYPE}))
BLOCKS_Weight = INT_TYPE
