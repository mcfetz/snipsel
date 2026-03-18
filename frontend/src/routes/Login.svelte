<script lang="ts">
  import Lock from '@animated-color-icons/lucide-svelte/Lock.svelte';
  import { api } from '../lib/api';
  import { currentUser } from '../lib/session';
  import { startAuthentication } from '@simplewebauthn/browser';
  import { onMount } from 'svelte';

  let mode = $state<'login' | 'register'>('login');
  let username = $state('');
  let email = $state('');
  let password = $state('');
  let otpCode = $state('');
  let isOtpStep = $state(false);
  let errorMessage = $state<string | null>(null);
  let busy = $state(false);
  let registrationEnabled = $state(true);

  onMount(async () => {
    try {
      const config = await api.getConfig();
      registrationEnabled = config.registration_enabled;
      if (!registrationEnabled && mode === 'register') {
        mode = 'login';
      }
    } catch (e) {
      console.error('Failed to fetch auth config:', e);
    }
  });

  async function submit() {
    errorMessage = null;
    busy = true;
    try {
      if (mode === 'login') {
        if (isOtpStep) {
          const res = await api.loginOtp(otpCode);
          currentUser.set(res.user);
        } else {
          const res = await api.login({ username, password });
          if (res.status === '2fa_required') {
            isOtpStep = true;
            busy = false;
            return;
          }
          if (res.user) {
            currentUser.set(res.user);
          }
        }
      } else {
        const res = await api.register({ username, email, password });
        currentUser.set(res.user);
      }
    } catch (e) {
      if (typeof e === 'object' && e && 'status' in e && (e as any).status === 401 && isOtpStep) {
        errorMessage = 'Invalid 2FA code';
      } else if (typeof e === 'object' && e && 'error' in e) {
        const err = e as { error: { message?: string } };
        errorMessage = err.error.message ?? 'Request failed';
      } else {
        errorMessage = 'Request failed';
      }
    } finally {
      busy = false;
    }
  }

  async function loginWithPasskey() {
    errorMessage = null;
    busy = true;
    try {
      // 1. Get options
      const options = await api.passkeys.loginBegin(username || '');
      
      // 2. Start authentication
      const authResp = await startAuthentication(options);
      
      // 3. Verify response
      const res = await api.passkeys.loginComplete(authResp);
      
      // 4. Get user
      currentUser.set(res.user);
    } catch (e: any) {
      console.error('Passkey login failed:', e);
      errorMessage = e.error?.message || e.message || 'Passkey login failed';
    } finally {
      busy = false;
    }
  }

  function toggleMode() {
    mode = mode === 'login' ? 'register' : 'login';
    isOtpStep = false;
    otpCode = '';
    errorMessage = null;
  }
</script>

<div class="mx-auto w-full max-w-sm pt-8 pb-12">
  <div class="flex flex-col items-center mb-8">
    <div class="grid h-16 w-16 place-items-center rounded-full bg-[#4f46e5]/10 mb-4 shadow-sm ring-1 ring-[#4f46e5]/20 dark:bg-indigo-900/30 dark:ring-indigo-500/30">
      <img src="/logo.svg" alt="snipsel logo" class="h-8 w-8 dark:brightness-110" />
    </div>
    <h1 class="text-3xl font-semibold tracking-tight text-slate-800 dark:text-slate-100">
      {isOtpStep ? 'Two-Factor Auth' : mode === 'login' ? 'Welcome back' : 'Create account'}
    </h1>
    <p class="mt-2 text-slate-500 dark:text-slate-400">
      {isOtpStep ? 'Enter the code from your app' : mode === 'login' ? 'Sign in to continue' : 'Sign up to get started'}
    </p>
  </div>

  <form class="space-y-5" onsubmit={(e) => { e.preventDefault(); submit(); }}>
    <div class="space-y-4 rounded-3xl border border-slate-200 bg-white/80 p-6 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      {#if !isOtpStep}
        <label class="block">
          <span class="mb-1.5 ml-1 block text-sm font-medium text-slate-600 dark:text-slate-400">Username</span>
          <input 
            class="w-full rounded-full border border-slate-200 bg-white px-5 py-3 text-lg shadow-sm outline-none ring-1 ring-black/5 transition-all focus:border-[#4f46e5] focus:ring-2 focus:ring-[#4f46e5]/20 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-500 dark:focus:ring-indigo-500/20" 
            bind:value={username} 
            autocomplete="username" 
          />
        </label>

        {#if mode === 'register'}
          <label class="block">
            <span class="mb-1.5 ml-1 block text-sm font-medium text-slate-600 dark:text-slate-400">Email</span>
            <input
              class="w-full rounded-full border border-slate-200 bg-white px-5 py-3 text-lg shadow-sm outline-none ring-1 ring-black/5 transition-all focus:border-[#4f46e5] focus:ring-2 focus:ring-[#4f46e5]/20 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-500 dark:focus:ring-indigo-500/20"
              bind:value={email}
              autocomplete="email"
              type="email"
            />
          </label>
        {/if}

        <label class="block">
          <span class="mb-1.5 ml-1 block text-sm font-medium text-slate-600 dark:text-slate-400">Password</span>
          <input
            class="w-full rounded-full border border-slate-200 bg-white px-5 py-3 text-lg shadow-sm outline-none ring-1 ring-black/5 transition-all focus:border-[#4f46e5] focus:ring-2 focus:ring-[#4f46e5]/20 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-500 dark:focus:ring-indigo-500/20"
            bind:value={password}
            autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
            type="password"
          />
        </label>
      {:else}
        <label class="block">
          <span class="mb-1.5 ml-1 block text-sm font-medium text-slate-600 dark:text-slate-400">6-digit Code</span>
          <input
            class="w-full rounded-full border border-slate-200 bg-white px-5 py-3 text-2xl tracking-[0.5em] text-center shadow-sm outline-none ring-1 ring-black/5 transition-all focus:border-[#4f46e5] focus:ring-2 focus:ring-[#4f46e5]/20 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-500 dark:focus:ring-indigo-500/20"
            bind:value={otpCode}
            inputmode="numeric"
            maxlength="6"
            placeholder="000000"
          />
        </label>
        <button 
          type="button"
          class="text-xs text-indigo-500 hover:text-indigo-600 ml-1"
          onclick={() => { isOtpStep = false; otpCode = ''; }}
        >
          ← Back to password
        </button>
      {/if}

      {#if errorMessage}
        <div class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-base text-red-700 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-400">
          {errorMessage}
        </div>
      {/if}
    </div>

    <div class="space-y-3">
      <button
        class="w-full rounded-full bg-[#4f46e5] px-4 py-3.5 text-lg font-semibold text-white shadow-lg transition-all hover:-translate-y-0.5 hover:bg-[#4338ca] hover:shadow-xl disabled:pointer-events-none disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-400"
        type="submit"
        disabled={busy || (isOtpStep && otpCode.length !== 6)}
      >
        {busy ? 'Please wait...' : isOtpStep ? 'Verify & Login' : mode === 'login' ? 'Login' : 'Register'}
      </button>

      {#if mode === 'login' && !isOtpStep}
        <button
          class="flex w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-3 text-base font-semibold text-slate-700 shadow-sm transition-all hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          type="button"
          onclick={loginWithPasskey}
          disabled={busy}
        >
          <Lock size={20} />
          Login with Passkey
        </button>
      {/if}
    </div>
  </form>

  {#if registrationEnabled}
    <button 
      class="mt-6 w-full rounded-full bg-[#4f46e5]/10 px-4 py-3.5 text-base font-semibold text-[#4f46e5] transition-all hover:bg-[#4f46e5]/20 dark:bg-indigo-500/20 dark:text-indigo-400 dark:hover:bg-indigo-500/30" 
      type="button" 
      onclick={toggleMode}
    >
      {mode === 'login' ? 'Need an account? Register' : 'Already have an account? Login'}
    </button>
  {/if}
</div>
