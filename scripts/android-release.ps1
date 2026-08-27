param(
    [ValidateSet('assembleRelease', 'bundleRelease')]
    [string]$Task = 'assembleRelease'
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$projectParent = Split-Path $projectRoot -Parent
$projectName = Split-Path $projectRoot -Leaf
$shortDrive = 'P'
$mapped = $false
$locationPushed = $false
$buildPath = Join-Path $projectRoot 'android'

function Set-AndroidToolchainEnvironment {
    # Android Studio가 설치된 일반적인 Windows 경로를 자동으로 사용한다.
    # 환경변수가 이미 있으면 사용자/CI 설정을 우선하며, 저장소에
    # machine-specific local.properties를 만들지 않는다.
    if (-not $env:JAVA_HOME -or -not (Test-Path (Join-Path $env:JAVA_HOME 'bin\java.exe'))) {
        $javaCandidates = @(
            @(
                (Join-Path ${env:ProgramFiles} 'Android\Android Studio\jbr'),
                (Join-Path ${env:LOCALAPPDATA} 'Programs\Android Studio\jbr')
            ) | Where-Object { $_ -and (Test-Path (Join-Path $_ 'bin\java.exe')) }
        )
        if ($javaCandidates.Count -gt 0) {
            $env:JAVA_HOME = $javaCandidates[0]
        }
    }

    if (-not $env:ANDROID_HOME -or -not (Test-Path (Join-Path $env:ANDROID_HOME 'platform-tools\adb.exe'))) {
        $sdkCandidates = @(
            @(
                $env:ANDROID_SDK_ROOT,
                $env:ANDROID_HOME,
                (Join-Path ${env:LOCALAPPDATA} 'Android\Sdk')
            ) | Where-Object { $_ -and (Test-Path (Join-Path $_ 'platform-tools\adb.exe')) }
        )
        if ($sdkCandidates.Count -gt 0) {
            $env:ANDROID_HOME = $sdkCandidates[0]
        }
    }

    if ($env:JAVA_HOME -and (Test-Path (Join-Path $env:JAVA_HOME 'bin\java.exe'))) {
        $env:Path = "$(Join-Path $env:JAVA_HOME 'bin');$env:Path"
    } else {
        throw 'JAVA_HOME을 찾지 못했습니다. Android Studio의 JDK 경로를 설정하세요.'
    }
    if ($env:ANDROID_HOME -and (Test-Path (Join-Path $env:ANDROID_HOME 'platform-tools\adb.exe'))) {
        $env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
        $env:Path = "$(Join-Path $env:ANDROID_HOME 'platform-tools');$env:Path"
    } else {
        throw 'ANDROID_HOME을 찾지 못했습니다. Android Studio SDK 경로를 설정하세요.'
    }
}

$existingShortDrive = Get-PSDrive -Name $shortDrive -ErrorAction SilentlyContinue
if ($existingShortDrive) {
    # 이미 같은 프로젝트 상위 폴더가 subst되어 있으면 그대로 재사용한다.
    # 네트워크 드라이브나 다른 경로를 덮어쓰지는 않는다.
    $substLine = @(& subst | Where-Object { $_ -match "^\s*${shortDrive}:.*=>\s*(.+)$" }) | Select-Object -First 1
    $existingTarget = $null
    if ($substLine) {
        $existingTarget = ($substLine -replace '^.*=>\s*', '').Trim()
    }
    $resolvedExistingTarget = $null
    if ($existingTarget) {
        try { $resolvedExistingTarget = (Resolve-Path $existingTarget -ErrorAction Stop).Path } catch { }
    }
    $resolvedProjectParent = (Resolve-Path $projectParent).Path
    if ($resolvedExistingTarget -and $resolvedExistingTarget.TrimEnd('\') -ieq $resolvedProjectParent.TrimEnd('\')) {
        $buildPath = "${shortDrive}:\$projectName\android"
    } else {
        throw "드라이브 ${shortDrive}:가 다른 경로에 사용 중입니다. 매핑을 정리한 뒤 다시 실행하세요."
    }
}

try {
    Set-AndroidToolchainEnvironment

    # React Native codegen + Ninja가 Windows MAX_PATH(260자)에 걸리지 않도록
    # 프로젝트를 임시로 짧은 드라이브 문자에 매핑한다. 프로젝트 파일은 이동하지 않는다.
    if ($existingShortDrive -and $buildPath.StartsWith("${shortDrive}:\", [System.StringComparison]::OrdinalIgnoreCase)) {
        $mapped = $false
        Write-Host "기존 ${shortDrive}: 프로젝트 매핑을 재사용합니다."
    } else {
        $substOutput = & subst "${shortDrive}:" $projectParent 2>&1
        if ($LASTEXITCODE -eq 0) {
            $mapped = $true
            $buildPath = "${shortDrive}:\$projectName\android"
        } else {
            # 회사 PC 정책/샌드박스에서 subst가 막혀도 release 검증을 진행한다.
            # 경로가 짧은 저장소에서는 직접 경로가 정상 동작하며, 긴 경로 오류는
            # Gradle의 원래 메시지로 확인할 수 있다.
            Write-Warning "${shortDrive}: 드라이브 매핑을 사용할 수 없어 원래 프로젝트 경로로 빌드합니다. $($substOutput -join ' ')"
        }
    }
    Push-Location $buildPath
    $locationPushed = $true

    if (-not $env:NODE_ENV) { $env:NODE_ENV = 'production' }
    if (-not $env:EXPO_PUBLIC_CATALOG_MODE) { $env:EXPO_PUBLIC_CATALOG_MODE = 'api' }
    if (-not $env:EXPO_PUBLIC_API_URL) {
        throw 'EXPO_PUBLIC_API_URL을 운영 API origin으로 설정한 뒤 실행하세요.'
    }

    # EAS와 로컬 Gradle이 동일한 운영 게이트를 통과하도록 한다. HTTPS가
    # 아니거나 localhost·placeholder 주소이면 서명 단계 전에 중단한다.
    $preflightScript = Join-Path $projectRoot 'scripts\release-preflight.mjs'
    & node $preflightScript
    if ($LASTEXITCODE -ne 0) { throw 'Android release 사전검사에 실패했습니다.' }

    $signingNames = @(
        'MYAPP_UPLOAD_STORE_FILE',
        'MYAPP_UPLOAD_STORE_PASSWORD',
        'MYAPP_UPLOAD_KEY_ALIAS',
        'MYAPP_UPLOAD_KEY_PASSWORD'
    )
    $missingSigning = @($signingNames | Where-Object {
        -not [Environment]::GetEnvironmentVariable($_)
    })
    if ($missingSigning.Count -gt 0) {
        throw "로컬 release 빌드에는 다음 서명 환경변수가 모두 필요합니다: $($missingSigning -join ', ')"
    }

    $gradleArgs = @(
        ":app:$Task",
        '--no-daemon',
        '--console=plain',
        "-PMYAPP_UPLOAD_STORE_FILE=$env:MYAPP_UPLOAD_STORE_FILE",
        "-PMYAPP_UPLOAD_STORE_PASSWORD=$env:MYAPP_UPLOAD_STORE_PASSWORD",
        "-PMYAPP_UPLOAD_KEY_ALIAS=$env:MYAPP_UPLOAD_KEY_ALIAS",
        "-PMYAPP_UPLOAD_KEY_PASSWORD=$env:MYAPP_UPLOAD_KEY_PASSWORD"
    )
    & .\gradlew.bat @gradleArgs
    if ($LASTEXITCODE -ne 0) { throw "Gradle 작업 실패: $LASTEXITCODE" }
}
finally {
    if ($locationPushed) { Pop-Location -ErrorAction SilentlyContinue }
    if ($mapped) { subst "${shortDrive}:" /d 2>$null }
}
