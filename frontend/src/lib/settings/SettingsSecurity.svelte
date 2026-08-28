<script lang="ts">
  import Lock from '@animated-color-icons/lucide-svelte/Lock.svelte';
  import Key from '@animated-color-icons/lucide-svelte/Key.svelte';
  import Check from '@animated-color-icons/lucide-svelte/Check.svelte';
  import { api, type ApiKey } from '../api';
  import { currentUser } from '../session';
  import { getContrastColor } from '../colors';
  import { startRegistration } from '@simplewebauthn/browser';

  interface Props {
    accent: string;
    isBusy: boolean;
  }

  let { accent, isBusy }: Props = $props();

  // Passcode
  let showPasscodeForm = $state(false);
  let passcode = $state('');
  let passcodeConfirmPassword = $state('');
  let passcodeError = $state('');
  let showPasscodeSaved = $state(false);
  let savingPasscode = $state(false);

  // OTP
  let isOtpSetupActive = $state(false);
  let isOtpDisableActive = $state(false);
  let otpSecret = $state('');
  let otpProvisioningUrl = $state('');
  let otpCodeInput = $state('');
  let otpSetupConfirmPassword = $state('');
  let otpDisableConfirmPassword = $state('');
  let securityError = $state('');
  let otpSetupError = $state('');
  let otpBusy = $state(false);

  // Passkeys
  let passkeys = $state<Array<{ id: string; name: string; created_at: string }>>([]);
  let isPasskeyAddActive = $state(false);
  let newPasskeyName = $state('');
  let passkeyError = $state('');
  let passkeyBusy = $state(false);

  // API Keys
  let apiKeys = $state<ApiKey[]>([]);
  let isApiKeyAddActive = $state(false);
  let newApiKeyName = $state('');
  let newApiKeyValue = $state('');
  let apiKeyError = $state('');
  let showCopiedKey = $state(false);
  let apiKeyBusy = $state(false);

  async function savePasscode() {
    if (passcode.length < 4) {
      passcodeError = 'Passcode must be at least 4 digits.';
      return;
    }
    if (!passcodeConfirmPassword) {
      passcodeError = 'Please confirm your account password.';
      return;
    }
    savingPasscode = true;
    passcodeError = '';
    try {
      const res = await api.auth.setPasscode(passcode, passcodeConfirmPassword);
      currentUser.set(res.user);
      showPasscodeSaved = true;
      setTimeout(() => {
        showPasscodeSaved = false;
        showPasscodeForm = false;
        passcode = '';
        passcodeConfirmPassword = '';
      }, 1500);
    } catch (err: any) {
      passcodeError = err?.message || 'Failed to update passcode.';
    } finally {
      savingPasscode = false;
    }
  }

  async function startOtpSetup() {
    otpBusy = true;
    securityError = '';
    try {
      const res = await api.twoFactor.generate();
      otpSecret = res.secret;
      otpProvisioningUrl = res.provisioning_url;
      isOtpSetupActive = true;
    } catch (err: any) {
      securityError = err?.message || 'Failed to initialize 2FA setup.';
    } finally {
      otpBusy = false;
    }
  }

  async function enableOtp() {
    if (!otpCodeInput || !otpSetupConfirmPassword) return;
    otpBusy = true;
    otpSetupError = '';
    try {
      const res = await api.twoFactor.enable(otpCodeInput, otpSetupConfirmPassword);
      currentUser.set(res.user);
      isOtpSetupActive = false;
      otpCodeInput = '';
      otpSetupConfirmPassword = '';
    } catch (err: any) {
      otpSetupError = err?.message || 'Invalid 2FA code or password.';
    } finally {
      otpBusy = false;
    }
  }

  async function disableOtp(password: string) {
    if (!password) return;
    otpBusy = true;
    securityError = '';
    try {
      const res = await api.twoFactor.disable(password);
      currentUser.set(res.user);
      isOtpDisableActive = false;
      otpDisableConfirmPassword = '';
    } catch (err: any) {
      securityError = err?.message || 'Failed to disable 2FA.';
    } finally {
      otpBusy = false;
    }
  }

  async function loadPasskeys() {
    try {
      const res = await api.auth.passkeys.list();
      passkeys = res.passkeys;
    } catch (err) {
      console.error('Failed to load passkeys:', err);
    }
  }

  async function addPasskey() {
    if (!newPasskeyName.trim()) return;
    passkeyBusy = true;
    passkeyError = '';
    try {
      const options = await api.auth.passkeys.registerOptions();
      const registrationResponse = await startRegistration({ optionsJSON: options });
      await api.auth.passkeys.registerVerify(newPasskeyName.trim(), registrationResponse);
      isPasskeyAddActive = false;
      newPasskeyName = '';
      await loadPasskeys();
    } catch (err: any) {
      passkeyError = err?.message || 'Failed to register passkey.';
    } finally {
      passkeyBusy = false;
    }
  }

  async function removePasskey(id: string) {
    if (!confirm('Are you sure you want to remove this passkey?')) return;
    try {
      await api.auth.passkeys.delete(id);
      await loadPasskeys();
    } catch (err) {
      console.error('Failed to remove passkey:', err);
    }
  }

  async function loadApiKeys() {
    try {
      const res = await api.apiKeys.list();
      apiKeys = res.api_keys;
    } catch (err) {
      console.error('Failed to load API keys:', err);
    }
  }

  async function createApiKey() {
    if (!newApiKeyName.trim()) return;
    apiKeyBusy = true;
    apiKeyError = '';
    try {
      const res = await api.apiKeys.create(newApiKeyName.trim());
      newApiKeyValue = res.key;
      await loadApiKeys();
    } catch (err: any) {
      apiKeyError = err?.message || 'Failed to create API key.';
    } finally {
      apiKeyBusy = false;
    }
  }

  async function revokeApiKey(id: string) {
    if (!confirm('Are you sure you want to revoke this API key? Applications using it will lose access immediately.')) return;
    try {
      await api.apiKeys.revoke(id);
      await loadApiKeys();
    } catch (err) {
      console.error('Failed to revoke API key:', err);
    }
  }

  function copyApiKey() {
    if (!newApiKeyValue) return;
    navigator.clipboard.writeText(newApiKeyValue).then(() => {
      showCopiedKey = true;
      setTimeout(() => {
        showCopiedKey = false;
      }, 2000);
    });
  }

  $effect(() => {
    if ($currentUser) {
      loadPasskeys();
      loadApiKeys();
    }
  });
</script>

<div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
  <div class="flex items-center gap-2 text-xs uppercase text-slate-500">
    <Lock label="" size={12} strokeWidth={2.5} />
    <span>Security</span>
  </div>

  <!-- Passcode -->
  <div class="border-b border-slate-100 pb-4 dark:border-white/5">
    {#if !showPasscodeForm}
      <div class="mt-3 flex items-center justify-between gap-4">
        <div>
          <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Personal Passcode</div>
          <div class="text-xs text-slate-500 dark:text-slate-400">
            {$currentUser?.passcode_set ? 'Passcode is active.' : 'Set a passcode to protect sensitive collections.'}
          </div>
        </div>
        <button
          class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
          style={`color: ${accent}`}
          type="button"
          onclick={() => {
            showPasscodeForm = true;
            passcodeError = '';
          }}
          disabled={isBusy || savingPasscode}
        >
          {$currentUser?.passcode_set ? 'Change' : 'Set Passcode'}
        </button>
      </div>
    {:else}
      <div class="mt-4 space-y-4 transition-all">
        <div>
          <label for="new-passcode" class="block text-sm font-medium text-slate-700 dark:text-slate-300">New 4-digit passcode</label>
          <input
            id="new-passcode"
            type="password"
            inputmode="numeric"
            maxlength="12"
            class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
            bind:value={passcode}
            oninput={(e) => passcode = e.currentTarget.value.replace(/\D/g, '')}
            placeholder="••••"
          />
        </div>
        <div>
          <label for="password-confirm" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Confirm account password</label>
          <input
            id="password-confirm"
            type="password"
            class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
            bind:value={passcodeConfirmPassword}
            placeholder="Your account password"
          />
        </div>

        {#if passcodeError}
          <div class="text-xs font-medium text-red-600 dark:text-red-400">{passcodeError}</div>
        {/if}

        <div class="flex items-center gap-2 pt-2">
          <button
            class="relative flex flex-1 items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-70"
            style={`background-color: ${accent}; color: ${getContrastColor(accent)}`}
            type="button"
            onclick={savePasscode}
            disabled={isBusy || savingPasscode || passcode.length < 4 || !passcodeConfirmPassword || showPasscodeSaved}
          >
            {#if savingPasscode}
              <div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
              <span>Saving...</span>
            {:else if showPasscodeSaved}
              <div class="flex items-center gap-2">
                <Check label="" size={18} strokeWidth={3} />
                <span>Saved!</span>
              </div>
            {:else}
              <span>Save Passcode</span>
            {/if}
          </button>
          <button
            class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
            style={`color: ${accent}`}
            type="button"
            onclick={() => {
              showPasscodeForm = false;
              passcode = '';
              passcodeConfirmPassword = '';
            }}
            disabled={isBusy || savingPasscode}
          >
            Cancel
          </button>
        </div>
      </div>
    {/if}
  </div>

  <!-- Two-Factor Authentication -->
  <div class="border-b border-slate-100 py-4 dark:border-white/5">
    <div class="flex items-center justify-between gap-4">
      <div>
        <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Two-Factor Authentication (OTP)</div>
        <div class="text-xs text-slate-500 dark:text-slate-400">
          {$currentUser?.otp_enabled ? 'Active. Extra security for your account.' : 'Enhance security by requiring a code from an authenticator app.'}
        </div>
      </div>
      {#if $currentUser?.otp_enabled}
        <button
          class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5 {isOtpDisableActive ? 'text-red-600 dark:text-red-400' : ''}"
          style={isOtpDisableActive ? '' : `color: ${accent}`}
          type="button"
          onclick={() => {
            isOtpDisableActive = !isOtpDisableActive;
            securityError = '';
            otpDisableConfirmPassword = '';
          }}
          disabled={isBusy || otpBusy}
        >
          {isOtpDisableActive ? 'Cancel' : 'Disable'}
        </button>
      {:else}
        <button
          class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
          style={`color: ${accent}`}
          type="button"
          onclick={startOtpSetup}
          disabled={isBusy || otpBusy}
        >
          Set up 2FA
        </button>
      {/if}
    </div>

    {#if securityError}
      <div class="mt-2 text-xs font-medium text-red-600 dark:text-red-400">{securityError}</div>
    {/if}

    {#if isOtpDisableActive}
      <div class="mt-4 space-y-4 rounded-xl bg-red-50/50 p-4 dark:bg-red-950/20">
        <div>
          <label for="otp-disable-pass" class="block text-sm font-medium text-red-800 dark:text-red-300">
            Confirm account password to disable 2FA
          </label>
          <input
            id="otp-disable-pass"
            type="password"
            class="mt-1 block w-full rounded-lg border border-red-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-red-900/30 dark:bg-slate-800"
            bind:value={otpDisableConfirmPassword}
            placeholder="Your account password"
          />
        </div>
        <button
          class="w-full rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-700 disabled:opacity-50"
          type="button"
          onclick={() => disableOtp(otpDisableConfirmPassword)}
          disabled={isBusy || otpBusy || !otpDisableConfirmPassword}
        >
          Confirm Disable 2FA
        </button>
      </div>
    {/if}

    {#if isOtpSetupActive}
      <div class="mt-4 space-y-4 rounded-xl bg-slate-50 p-4 dark:bg-white/5">
        <div class="text-sm font-medium">Scan this QR code in your app</div>
        <div class="flex justify-center rounded-lg bg-white p-2">
          <img src={`/api/auth/2fa/qr?provisioning_url=${encodeURIComponent(otpProvisioningUrl)}`} alt="2FA QR Code" class="h-48 w-48" />
        </div>
        <div class="text-center text-xs text-slate-500">
          Or enter manually: <code class="bg-slate-200 px-1 dark:bg-white/10">{otpSecret}</code>
        </div>

        <div class="space-y-3">
          <div>
            <label for="otp-code" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Enter code from app</label>
            <input
              id="otp-code"
              type="text"
              inputmode="numeric"
              maxlength="6"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
              bind:value={otpCodeInput}
              placeholder="000000"
            />
          </div>
          <div>
            <label for="otp-password-confirm" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Confirm account password</label>
            <input
              id="otp-password-confirm"
              type="password"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
              bind:value={otpSetupConfirmPassword}
              placeholder="Your account password"
            />
          </div>
        </div>

        {#if otpSetupError}
          <div class="text-xs font-medium text-red-600 dark:text-red-400">{otpSetupError}</div>
        {/if}

        <div class="flex gap-2">
          <button
            class="flex-1 rounded-full px-4 py-2 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-70"
            style={`background-color: ${accent}; color: ${getContrastColor(accent)}`}
            type="button"
            onclick={enableOtp}
            disabled={isBusy || otpBusy || otpCodeInput.length < 6 || !otpSetupConfirmPassword}
          >
            {otpBusy ? 'Enabling...' : 'Enable 2FA'}
          </button>
          <button
            class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
            style={`color: ${accent}`}
            type="button"
            onclick={() => {
              isOtpSetupActive = false;
              otpCodeInput = '';
              otpSetupConfirmPassword = '';
            }}
            disabled={isBusy || otpBusy}
          >
            Cancel
          </button>
        </div>
      </div>
    {/if}
  </div>

  <!-- Passkeys -->
  <div class="border-b border-slate-100 py-4 dark:border-white/5">
    <div class="flex items-center justify-between gap-4">
      <div>
        <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Passkeys</div>
        <div class="text-xs text-slate-500 dark:text-slate-400">
          Use biometric or hardware keys to log in without a password.
        </div>
      </div>
      <button
        class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
        style={`color: ${accent}`}
        type="button"
        onclick={() => {
          isPasskeyAddActive = true;
          passkeyError = '';
          loadPasskeys();
        }}
        disabled={isBusy || passkeyBusy}
      >
        Add Key
      </button>
    </div>

    {#if isPasskeyAddActive}
      <div class="mt-4 space-y-4 rounded-xl bg-slate-50 p-4 dark:bg-white/5">
        <div>
          <label for="passkey-name" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Key Name</label>
          <input
            id="passkey-name"
            type="text"
            class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
            bind:value={newPasskeyName}
            placeholder="e.g. MacBook Air, YubiKey"
          />
        </div>

        {#if passkeyError}
          <div class="text-xs font-medium text-red-600 dark:text-red-400">{passkeyError}</div>
        {/if}

        <div class="flex gap-2">
          <button
            class="flex-1 rounded-full px-4 py-2 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-70"
            style={`background-color: ${accent}; color: ${getContrastColor(accent)}`}
            type="button"
            onclick={addPasskey}
            disabled={isBusy || passkeyBusy || !newPasskeyName}
          >
            {passkeyBusy ? 'Registering...' : 'Continue'}
          </button>
          <button
            class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
            style={`color: ${accent}`}
            type="button"
            onclick={() => {
              isPasskeyAddActive = false;
              newPasskeyName = '';
            }}
            disabled={isBusy || passkeyBusy}
          >
            Cancel
          </button>
        </div>
      </div>
    {/if}

    {#if passkeys.length > 0}
      <div class="mt-4 space-y-2">
        {#each passkeys as pk (pk.id)}
          <div class="flex items-center justify-between rounded-lg border border-slate-100 bg-white/50 px-3 py-2 dark:border-white/5 dark:bg-slate-900/50">
            <div class="flex items-center gap-2">
              <Key label="" size={16} className="text-slate-400" />
              <span class="text-sm font-medium">{pk.name}</span>
            </div>
            <button
              class="rounded-full bg-red-600/10 px-3 py-1.5 text-xs font-bold text-red-600 transition-all hover:bg-red-600 hover:text-white dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-600 dark:hover:text-white"
              type="button"
              onclick={() => removePasskey(pk.id)}
              disabled={isBusy}
            >
              Delete
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- API Keys -->
  <div class="pt-4">
    <div class="flex items-center justify-between gap-4">
      <div>
        <div class="text-sm font-medium text-slate-900 dark:text-slate-100">API Keys</div>
        <div class="text-xs text-slate-500 dark:text-slate-400">
          Create API keys for integrations like iOS Shortcuts or browser extensions.
        </div>
      </div>
      <button
        class="rounded-full border border-slate-200 bg-white px-6 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
        style={`color: ${accent}`}
        type="button"
        onclick={() => {
          isApiKeyAddActive = true;
          apiKeyError = '';
          newApiKeyName = '';
          newApiKeyValue = '';
        }}
        disabled={isBusy || apiKeyBusy}
      >
        Create Key
      </button>
    </div>

    {#if isApiKeyAddActive}
      <div class="mt-4 space-y-4 rounded-xl bg-slate-50 p-4 dark:bg-white/5">
        {#if newApiKeyValue}
          <div class="space-y-3">
            <div class="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-900/30 dark:bg-amber-950/20">
              <div class="mb-2 text-sm font-medium text-amber-800 dark:text-amber-300">
                Copy your API key now!
              </div>
              <div class="mb-2 text-xs text-amber-700 dark:text-amber-400">
                This is the only time you will see this key. Store it securely.
              </div>
              <div class="flex items-center gap-2">
                <code class="flex-1 break-all rounded bg-white px-2 py-1.5 font-mono text-xs dark:bg-slate-900">
                  {newApiKeyValue}
                </code>
                <button
                  class="shrink-0 rounded-lg bg-amber-100 px-3 py-1.5 text-xs font-medium text-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
                  type="button"
                  onclick={copyApiKey}
                >
                  {showCopiedKey ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>
            <button
              class="w-full rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
              type="button"
              onclick={() => {
                isApiKeyAddActive = false;
                newApiKeyValue = '';
              }}
            >
              Done
            </button>
          </div>
        {:else}
          <div>
            <label for="apikey-name" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Key Name</label>
            <input
              id="apikey-name"
              type="text"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
              bind:value={newApiKeyName}
              placeholder="e.g. iOS Shortcut, CLI tool"
            />
          </div>

          {#if apiKeyError}
            <div class="text-xs font-medium text-red-600 dark:text-red-400">{apiKeyError}</div>
          {/if}

          <div class="flex gap-2">
            <button
              class="flex-1 rounded-full px-4 py-2 text-sm font-bold shadow-xl transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-70"
              style={`background-color: ${accent}; color: ${getContrastColor(accent)}`}
              type="button"
              onclick={createApiKey}
              disabled={isBusy || apiKeyBusy || !newApiKeyName}
            >
              {apiKeyBusy ? 'Creating...' : 'Create'}
            </button>
            <button
              class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-white/5"
              style={`color: ${accent}`}
              type="button"
              onclick={() => {
                isApiKeyAddActive = false;
                newApiKeyName = '';
              }}
              disabled={isBusy || apiKeyBusy}
            >
              Cancel
            </button>
          </div>
        {/if}
      </div>
    {/if}

    {#if apiKeys.length > 0}
      <div class="mt-4 space-y-2">
        {#each apiKeys as key (key.id)}
          <div class="flex items-center justify-between rounded-lg border border-slate-100 bg-white/50 px-3 py-2 dark:border-white/5 dark:bg-slate-900/50">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <Key label="" size={16} className="text-slate-400 shrink-0" />
                <span class="truncate text-sm font-medium">{key.name}</span>
                <span class="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] text-slate-500 dark:bg-white/10 dark:text-slate-400">
                  {key.prefix}...
                </span>
              </div>
              <div class="mt-0.5 text-xs text-slate-400">
                Created {new Date(key.created_at).toLocaleDateString()}
                {#if key.last_used_at}
                  · Last used {new Date(key.last_used_at).toLocaleDateString()}
                {:else}
                  · Never used
                {/if}
              </div>
            </div>
            <button
              class="rounded-full bg-red-600/10 px-3 py-1.5 text-xs font-bold text-red-600 transition-all hover:bg-red-600 hover:text-white dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-600 dark:hover:text-white"
              type="button"
              onclick={() => revokeApiKey(key.id)}
              disabled={isBusy}
            >
              Revoke
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
