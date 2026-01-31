import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { useTelegram } from '../hooks/useTelegram';

const languages = [
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'uk', name: 'Українська', flag: '🇺🇦' },
];

const timezones = [
  { code: 'Europe/Moscow', name: 'Москва', offset: 'UTC+3' },
  { code: 'Europe/Kiev', name: 'Киев', offset: 'UTC+2' },
  { code: 'Asia/Almaty', name: 'Алматы', offset: 'UTC+6' },
  { code: 'Europe/London', name: 'Лондон', offset: 'UTC+0' },
  { code: 'America/New_York', name: 'Нью-Йорк', offset: 'UTC-5' },
];

export function Settings() {
  const navigate = useNavigate();
  const { state, actions } = useApp();
  const { showBackButton, hideBackButton, hapticFeedback, user } = useTelegram();
  const [showLanguages, setShowLanguages] = useState(false);
  const [showTimezones, setShowTimezones] = useState(false);

  useEffect(() => {
    showBackButton(() => navigate(-1));
    return () => hideBackButton();
  }, []);

  const handleToggleNotifications = async () => {
    hapticFeedback('impact');
    await actions.updateSettings({
      notifications_enabled: !state.user?.notifications_enabled,
    });
  };

  const handleLanguageChange = async (code) => {
    hapticFeedback('impact');
    await actions.updateSettings({ language: code });
    setShowLanguages(false);
  };

  const handleTimezoneChange = async (code) => {
    hapticFeedback('impact');
    await actions.updateSettings({ timezone: code });
    setShowTimezones(false);
  };

  const currentLanguage = languages.find((l) => l.code === state.user?.language) || languages[0];
  const currentTimezone = timezones.find((t) => t.code === state.user?.timezone) || timezones[0];

  const stats = [
    { icon: '✅', label: 'Выполнено', value: state.stats?.completed || 0, color: 'from-emerald-500 to-teal-500' },
    { icon: '🔥', label: 'Серия дней', value: state.stats?.current_streak || 0, color: 'from-amber-500 to-orange-500' },
    { icon: '📊', label: 'Успешность', value: `${state.stats?.completion_rate || 0}%`, color: 'from-violet-500 to-purple-500' },
    { icon: '⭐', label: 'Лучшая серия', value: state.stats?.best_streak || 0, color: 'from-pink-500 to-rose-500' },
  ];

  return (
    <div className="min-h-screen pb-8 relative">
      {/* Космический фон */}
      <div className="cosmic-bg" />
      <div className="nebula" />

      {/* Header */}
      <header className="sticky top-0 z-20 glass-strong">
        <div className="px-5 py-4">
          <h1 className="text-xl font-bold text-white animate-fade-in">
            ⚙️ Настройки
          </h1>
        </div>
      </header>

      <main className="px-5 py-6 space-y-8 relative z-10">
        {/* Profile Card */}
        <section className="animate-slide-up">
          <div className="glass-card p-6">
            <div className="flex items-center gap-4">
              <div className="w-20 h-20 rounded-2xl gradient-purple glow-purple
                              flex items-center justify-center animate-float">
                <span className="text-3xl font-bold text-white">
                  {user?.first_name?.[0] || state.user?.first_name?.[0] || '?'}
                </span>
              </div>
              <div>
                <div className="text-xl font-bold text-white">
                  {user?.first_name || state.user?.first_name} {user?.last_name || state.user?.last_name}
                </div>
                <div className="text-white/50">
                  @{user?.username || state.user?.username || 'username'}
                </div>
                <div className="text-violet-400 text-sm mt-1">
                  Premium User ✨
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Grid */}
        <section className="animate-slide-up delay-100">
          <h2 className="text-sm font-medium text-white/50 uppercase tracking-wider mb-4 px-1">
            📊 Статистика
          </h2>
          <div className="grid grid-cols-2 gap-3">
            {stats.map((stat, idx) => (
              <div
                key={stat.label}
                className="glass-card p-4 animate-scale-in"
                style={{ animationDelay: `${(idx + 2) * 100}ms` }}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-10 h-10 rounded-xl bg-gradient-to-r ${stat.color}
                                  flex items-center justify-center`}>
                    <span className="text-lg">{stat.icon}</span>
                  </div>
                  <span className="text-white/60 text-sm">{stat.label}</span>
                </div>
                <div className="text-2xl font-bold text-white">{stat.value}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Settings List */}
        <section className="animate-slide-up delay-200">
          <h2 className="text-sm font-medium text-white/50 uppercase tracking-wider mb-4 px-1">
            ⚙️ Настройки
          </h2>
          <div className="glass-card divide-y divide-white/5 overflow-hidden">
            {/* Language */}
            <SettingsItem
              icon="🌐"
              iconBg="from-blue-500 to-cyan-500"
              label="Язык"
              value={`${currentLanguage.flag} ${currentLanguage.name}`}
              onClick={() => setShowLanguages(!showLanguages)}
              expanded={showLanguages}
            />
            {showLanguages && (
              <div className="bg-white/[0.02] animate-slide-down">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => handleLanguageChange(lang.code)}
                    className="w-full p-4 flex items-center justify-between
                               active:bg-white/5 transition-colors"
                  >
                    <span className="text-white/80">{lang.flag} {lang.name}</span>
                    {state.user?.language === lang.code && (
                      <span className="text-violet-400">✓</span>
                    )}
                  </button>
                ))}
              </div>
            )}

            {/* Timezone */}
            <SettingsItem
              icon="🕐"
              iconBg="from-violet-500 to-purple-500"
              label="Часовой пояс"
              value={`${currentTimezone.name} (${currentTimezone.offset})`}
              onClick={() => setShowTimezones(!showTimezones)}
              expanded={showTimezones}
            />
            {showTimezones && (
              <div className="bg-white/[0.02] animate-slide-down">
                {timezones.map((tz) => (
                  <button
                    key={tz.code}
                    onClick={() => handleTimezoneChange(tz.code)}
                    className="w-full p-4 flex items-center justify-between
                               active:bg-white/5 transition-colors"
                  >
                    <span className="text-white/80">{tz.name} <span className="text-white/40">({tz.offset})</span></span>
                    {state.user?.timezone === tz.code && (
                      <span className="text-violet-400">✓</span>
                    )}
                  </button>
                ))}
              </div>
            )}

            {/* Notifications */}
            <div className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-rose-500 to-pink-500
                                flex items-center justify-center">
                  <span className="text-lg">🔔</span>
                </div>
                <div>
                  <div className="text-white font-medium">Уведомления</div>
                  <div className="text-white/40 text-sm">
                    {state.user?.notifications_enabled ? 'Включены' : 'Выключены'}
                  </div>
                </div>
              </div>

              {/* iOS Toggle */}
              <button
                onClick={handleToggleNotifications}
                className={`w-14 h-8 rounded-full transition-all duration-300 flex items-center px-1
                           ${state.user?.notifications_enabled
                             ? 'bg-gradient-to-r from-emerald-500 to-teal-500'
                             : 'bg-white/10'
                           }`}
              >
                <div
                  className={`w-6 h-6 bg-white rounded-full shadow-lg transition-transform duration-300
                             ${state.user?.notifications_enabled ? 'translate-x-6' : 'translate-x-0'}`}
                />
              </button>
            </div>
          </div>
        </section>

        {/* About */}
        <section className="text-center pt-8 animate-fade-in delay-400">
          <div className="glass-card p-6 inline-block mx-auto">
            <div className="text-4xl mb-3">🚀</div>
            <div className="text-white font-semibold">LoginovRemind</div>
            <div className="text-white/40 text-sm">Version 1.0.0</div>
          </div>
          <p className="text-white/30 text-xs mt-4">
            Made with 💜 by Loginov
          </p>
        </section>
      </main>
    </div>
  );
}

// Settings Item Component
function SettingsItem({ icon, iconBg, label, value, onClick, expanded }) {
  return (
    <button
      onClick={onClick}
      className="w-full p-4 flex items-center justify-between active:bg-white/5 transition-colors"
    >
      <div className="flex items-center gap-4">
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-r ${iconBg}
                        flex items-center justify-center`}>
          <span className="text-lg">{icon}</span>
        </div>
        <div className="text-left">
          <div className="text-white font-medium">{label}</div>
          <div className="text-white/40 text-sm">{value}</div>
        </div>
      </div>
      <svg
        className={`w-5 h-5 text-white/40 transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  );
}