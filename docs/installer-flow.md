# CCNotify Installer Flow

## Single-Command Architecture: `uvx ccnotify install`

```mermaid
flowchart TD
    Start([uvx ccnotify install]) --> CheckExisting{Check existing installation}
    
    CheckExisting -->|None found| FirstInstall[First-time installation]
    CheckExisting -->|Found| ExistingInstall[Existing installation detected]
    
    %% First-time installation path
    FirstInstall --> Welcome[Show welcome message]
    Welcome --> ChooseTTS{Choose TTS provider}
    
    ChooseTTS -->|Kokoro| KokoroSetup[Setup Kokoro]
    ChooseTTS -->|ElevenLabs| ElevenLabsSetup[Setup ElevenLabs] 
    ChooseTTS -->|None/Skip| NoTTSSetup[No TTS setup]
    
    KokoroSetup --> DownloadModels{Download models now?}
    DownloadModels -->|Yes| DownloadKokoro[Download Kokoro models]
    DownloadModels -->|No| SkipModels[Skip model download]
    DownloadKokoro --> CreateConfig[Create config file]
    SkipModels --> CreateConfig
    
    ElevenLabsSetup --> CreateConfig
    NoTTSSetup --> CreateConfig
    
    CreateConfig --> InstallHooks[Install Claude hooks]
    InstallHooks --> FirstComplete[✅ Installation complete]
    
    %% Existing installation path  
    ExistingInstall --> ShowStatus[Show current config/version]
    ShowStatus --> CheckUpdates{Check for updates}
    
    CheckUpdates -->|Script newer| OfferScriptUpdate{Update ccnotify script?}
    CheckUpdates -->|Script same| CheckModelUpdates
    
    OfferScriptUpdate -->|Yes| UpdateScript[Update script files]
    OfferScriptUpdate -->|No| CheckModelUpdates{Check model updates?}
    
    UpdateScript --> CheckModelUpdates
    CheckModelUpdates -->|Kokoro configured| CheckKokoroVersion{Newer Kokoro models?}
    CheckModelUpdates -->|No Kokoro| OfferOverwrite
    
    CheckKokoroVersion -->|Yes| OfferModelUpdate{Update models?}
    CheckKokoroVersion -->|No| OfferOverwrite{Overwrite anyway?}
    
    OfferModelUpdate -->|Yes| UpdateModels[Download new models]
    OfferModelUpdate -->|No| OfferOverwrite
    
    UpdateModels --> UpdateComplete[✅ Update complete]
    
    OfferOverwrite -->|Yes| ReconfigureTTS{Reconfigure TTS?}
    OfferOverwrite -->|No| NoChanges[No changes made]
    
    ReconfigureTTS -->|Yes| ChooseTTS
    ReconfigureTTS -->|No| OverwriteScript[Overwrite script files]
    OverwriteScript --> OverwriteComplete[✅ Overwrite complete]
    
    %% Terminal states
    FirstComplete --> End([Done])
    UpdateComplete --> End
    OverwriteComplete --> End  
    NoChanges --> End
```

## Implementation Strategy

### Version Detection
- Check installed script version vs package version
- Check Kokoro model version if configured
- Preserve user configuration unless explicitly changing

### Update Logic
- Conservative: Only update what's necessary
- Preserve: Keep user configurations and preferences  
- Clear: Always explain what will be changed