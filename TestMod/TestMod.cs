﻿using RL2.ModLoader;
using System;
using UnityEngine;

namespace TestMod;

public class TestMod : Mod
{
    public override string Name { get => "TestMod"; }

    public override void Load()
    {
        Messenger<ModMessenger, ModLoaderEvent>.AddListener(ModLoaderEvent.Load, OnLoad);
        Messenger<ModMessenger, ModLoaderEvent>.AddListener(ModLoaderEvent.Unload, OnUnload);
        Log($"{Name} loaded!");
    }

    public void OnLoad(MonoBehaviour sender, EventArgs eventArgs)
    {
        Log("Cawabunga");
    }

    public void OnUnload(MonoBehaviour sender, EventArgs eventArgs)
    {
        Log($"{Name} unloaded!");
    }

    [Command("fps")]
    public static void ShowFpsCommand()
    {
        Messenger<DebugMessenger, DebugEvent>.Broadcast(DebugEvent.ToggleFPSCounter, null, null);
    }

    public new static void Log(string message)
    {
        Debug.Log($"[TestMod]: {message}");
    }
}