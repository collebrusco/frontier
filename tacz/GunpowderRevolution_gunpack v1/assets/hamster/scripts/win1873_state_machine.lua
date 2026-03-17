local default = require("hamster_hamster_state_machine")
local GUN_KICK_TRACK_LINE = default.GUN_KICK_TRACK_LINE
local STATIC_TRACK_LINE = default.STATIC_TRACK_LINE
local BOLT_CAUGHT_TRACK = default.BOLT_CAUGHT_TRACK
local main_track_states = default.main_track_states
local MAIN_TRACK = default.MAIN_TRACK
local BASE_TRACK = default.BASE_TRACK

local bolt_caught_states = default.bolt_caught_states

local ADS_states = default.ADS_states

local base_track_state = setmetatable({
    normal = {},
    transformed = {}
}, {__index = default.base_track_state})

local gun_kick_state = setmetatable({}, {__index = default.gun_kick_state})
local reload_state = {
    emptyload = -1,
    need_ammo = 0,
    loaded_ammo = 0
}
local leverreload_state = {}

local start_state = setmetatable({}, {__index = main_track_states.start})
local idle_state = setmetatable({}, {__index = main_track_states.idle})
local normal = setmetatable({}, {__index = bolt_caught_states.normal})
local bolt_caught = setmetatable({}, {__index = bolt_caught_states.bolt_caught})

local adsnormal = setmetatable({}, {__index = ADS_states.normal})

function base_track_state.normal.entry(this, context)
    if (context:isStopped(context:getTrack(STATIC_TRACK_LINE, BASE_TRACK)) or context:isHolding(context:getTrack(STATIC_TRACK_LINE, BASE_TRACK))) then
        context:runAnimation("static_idle", context:getTrack(STATIC_TRACK_LINE, BASE_TRACK), false, PLAY_ONCE_HOLD, 0)
    end
end

function base_track_state.normal.transition(this, context)
    if(context:getFireMode() == AUTO and context:isStopped(context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK))) then
        context:runAnimation("normal_transition", context:getTrack(STATIC_TRACK_LINE, BASE_TRACK), false, PLAY_ONCE_HOLD, 0.2)
        return this.base_track_state.transformed
    end
end

function base_track_state.transformed.entry(this, context)
    if (context:isStopped(context:getTrack(STATIC_TRACK_LINE, BASE_TRACK)) or context:isHolding(context:getTrack(STATIC_TRACK_LINE, BASE_TRACK))) then
        context:runAnimation("static_idle_lever", context:getTrack(STATIC_TRACK_LINE, BASE_TRACK), false, PLAY_ONCE_HOLD, 0)
    end
end

function base_track_state.transformed.transition(this, context)
    if(context:getFireMode() == SEMI and context:isStopped(context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK))) then
        context:runAnimation("lever_transition", context:getTrack(STATIC_TRACK_LINE, BASE_TRACK), false, PLAY_ONCE_HOLD, 0.2)
        return this.base_track_state.normal
    end
end

function normal.update(this, context)
    if (not context:hasBulletInBarrel()) then
        context:trigger(this.INPUT_BOLT_CAUGHT)
    end
end

function bolt_caught.update(this, context)
    if (context:hasBulletInBarrel()) then
        context:trigger(this.INPUT_BOLT_NORMAL)
    end
end

function gun_kick_state.transition(this, context, input)
    if (input == INPUT_SHOOT) then
        local track = context:findIdleTrack(GUN_KICK_TRACK_LINE, false)
        context:runAnimation("shoot", track, true, PLAY_ONCE_STOP, 0)
        if (context:getAttachment("SCOPE") ~= "tacz:empty") then
            context:runAnimation("shoot_scope", track, true, PLAY_ONCE_STOP, 0)
        else
            context:runAnimation("shoot", track, true, PLAY_ONCE_STOP, 0)
        end
        if (context:getAimingProgress() == 0) then
            main_track_states.shoot_mode = 1
        else
            main_track_states.shoot_mode = 0
        end
    end
    return nil
end

function start_state.transition(this, context, input)
    -- 玩家手里拿到枪的那一瞬间会自动输入一个 draw 的信号,不用手动触发
    if (input == INPUT_DRAW) then
        -- 收到 draw 信号后在主轨道行的主轨道上播放掏枪动画,然后转到闲置态
        if (context:getFireMode() == SEMI) then
            context:runAnimation("draw", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0)
        else
            context:runAnimation("draw_lever", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0)
        end
        return this.main_track_states.idle
    end
end

function idle_state.transition(this, context, input)
    if (input == INPUT_PUT_AWAY) then
        local put_away_time = context:getPutAwayTime()
        -- 此处获取的轨道是位于主轨道行上的主轨道
        local track = context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK)
        -- 播放 put_away 动画,并且将其过渡时长设为从上下文里传入的 put_away_time * 0.75
        if (context:getFireMode() == SEMI) then
            context:runAnimation("put_away", track, false, PLAY_ONCE_HOLD, put_away_time * 0.75)
        else
            context:runAnimation("put_away_lever", track, false, PLAY_ONCE_HOLD, put_away_time * 0.75)
        end
        -- 设定动画进度为最后一帧
        context:setAnimationProgress(track, 1, true)
        -- 将动画进度向前拨动 {put_away_time}
        context:adjustAnimationProgress(track, -put_away_time, false)
        return this.main_track_states.idle
    end
    if (input == INPUT_INSPECT) then
        if (context:getFireMode() == SEMI) then
            context:runAnimation("inspect", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
        else
            context:runAnimation("inspect_lever", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
        end
        return this.main_track_states.inspect
    end
    if (input == INPUT_RELOAD) then
        if (context:getFireMode() == SEMI) then
            return this.main_track_states.reload
        else
            return this.main_track_states.leverreload
        end
    end
    if (input == INPUT_BOLT) then
        if (context:getFireMode() == AUTO) then
            if (main_track_states.shoot_mode == 1) then
                context:runAnimation("bolt_lever", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
                context:runAnimation("bolt_charge_lever", context:getTrack(STATIC_TRACK_LINE, BOLT_CAUGHT_TRACK), false, PLAY_ONCE_STOP, 0.2)
            else
                if (context:getAttachment("SCOPE") ~= "tacz:empty") then
                    context:runAnimation("bolt_1_scope", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
                else
                    context:runAnimation("bolt_1", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
                end
                context:runAnimation("bolt_charge", context:getTrack(STATIC_TRACK_LINE, BOLT_CAUGHT_TRACK), false, PLAY_ONCE_STOP, 0.2)
            end
        else
            if (context:getAttachment("SCOPE") ~= "tacz:empty") then
                context:runAnimation("bolt_scope", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            else
                context:runAnimation("bolt", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            end
            context:runAnimation("bolt_charge", context:getTrack(STATIC_TRACK_LINE, BOLT_CAUGHT_TRACK), false, PLAY_ONCE_STOP, 0.2)
        end
        return this.main_track_states.idle
    end
    return main_track_states.idle.transition(this, context, input)
end

function reload_state.entry(this, context)
    local isNoAmmo = not context:hasBulletInBarrel()
    if (isNoAmmo) then
        this.main_track_states.reload.emptyload = 1
        context:runAnimation("reload_start", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_HOLD, 0.2)
    else
        context:runAnimation("reload_start", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_HOLD, 0.2)
    end
    this.main_track_states.reload.need_ammo = context:getMaxAmmoCount() - context:getAmmoCount()
    this.main_track_states.reload.loaded_ammo = 0
end

function reload_state.update(this, context)
    if (this.main_track_states.reload.loaded_ammo > this.main_track_states.reload.need_ammo or not context:hasAmmoToConsume()) then
        context:trigger(this.INPUT_RELOAD_RETREAT)
    else
        local track = context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK)
        -- 等待 intro 结束，然后循环播放 loop 动画
        if(context:isHolding(track)) then
            if(this.main_track_states.reload.emptyload == 1) then
                context:runAnimation("reload_loop", track, false, PLAY_ONCE_HOLD, 0.2)
                this.main_track_states.reload.loaded_ammo = this.main_track_states.reload.loaded_ammo + 1
            else
                context:runAnimation("reload_loop", track, false, PLAY_ONCE_HOLD, 0.2)
                this.main_track_states.reload.loaded_ammo = this.main_track_states.reload.loaded_ammo + 1
            end
        end
    end
end

function reload_state.transition(this, context, input)
    if (input == this.INPUT_RELOAD_RETREAT or input == INPUT_CANCEL_RELOAD) then
        if(this.main_track_states.reload.emptyload == 1) then
            context:runAnimation("reload_end_empty", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            this.main_track_states.reload.emptyload = 0
        else
            context:runAnimation("reload_end", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
        end
        return this.main_track_states.idle
    end
    return this.main_track_states.idle.transition(this, context, input)
end

function leverreload_state.entry(this, context)
    local isNoAmmo = not context:hasBulletInBarrel()
    if (isNoAmmo) then
        this.main_track_states.reload.emptyload = 1
        context:runAnimation("reload_start_lever", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_HOLD, 0.2)
    else
        context:runAnimation("reload_start_lever", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_HOLD, 0.2)
    end
    this.main_track_states.reload.need_ammo = context:getMaxAmmoCount() - context:getAmmoCount()
    this.main_track_states.reload.loaded_ammo = 0
end

function leverreload_state.update(this, context)
    if (this.main_track_states.reload.loaded_ammo > this.main_track_states.reload.need_ammo or not context:hasAmmoToConsume()) then
        context:trigger(this.INPUT_RELOAD_RETREAT)
    else
        local track = context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK)
        -- 等待 intro 结束，然后循环播放 loop 动画
        if(context:isHolding(track)) then
            if(this.main_track_states.reload.emptyload == 1) then
                context:runAnimation("reload_loop", track, false, PLAY_ONCE_HOLD, 0.2)
                this.main_track_states.reload.loaded_ammo = this.main_track_states.reload.loaded_ammo + 1
            else
                context:runAnimation("reload_loop", track, false, PLAY_ONCE_HOLD, 0.2)
                this.main_track_states.reload.loaded_ammo = this.main_track_states.reload.loaded_ammo + 1
            end
        end
    end
end

function leverreload_state.transition(this, context, input)
    if (input == this.INPUT_RELOAD_RETREAT or input == INPUT_CANCEL_RELOAD) then
        if(this.main_track_states.reload.emptyload == 1) then
            context:runAnimation("reload_end_empty_lever", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            this.main_track_states.reload.emptyload = 0
        else
            context:runAnimation("reload_end_lever", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
        end
        return this.main_track_states.idle
    end
    return this.main_track_states.idle.transition(this, context, input)
end

-- 转出不瞄准状态
function adsnormal.transition(this, context, input)
    -- 接收到上文 update 方法的输入，则转到瞄准状态
    if (input == this.INPUT_AIM and context:getFireMode() == AUTO) then
        return this.ADS_states.aiming
    end
end

local M = setmetatable({
    main_track_states = setmetatable({
    	start = start_state,
        reload = reload_state,
        leverreload = leverreload_state,
        idle = idle_state
    }, {__index = main_track_states}),
    bolt_caught_states = setmetatable({
        normal = normal,
        bolt_caught = bolt_caught
    }, {__index = bolt_caught_states}),
    ADS_states = setmetatable({
        normal = adsnormal,
    }, {__index = ADS_states}),
    base_track_state = base_track_state,
    gun_kick_state = gun_kick_state,
    INPUT_RELOAD_RETREAT = "reload_retreat",
}, {__index = default})

function M:initialize(context)
    default.initialize(self, context)
    self.main_track_states.reload.emptyload = -1
    self.main_track_states.reload.need_ammo = 0
    self.main_track_states.reload.loaded_ammo = 0
end

function M:states()
    return {
        self.base_track_state.normal,
        self.bolt_caught_states.normal,
        self.main_track_states.start,
        self.gun_kick_state,
        self.ADS_states.normal,
        self.movement_track_states.idle
    }
end

return M