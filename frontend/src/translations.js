// All UI text the dashboard shows, in three languages.
// To add a new UI string anywhere: add the key here in all three
// languages, then use t('thatKey') in Dashboard.jsx.
export const translations = {
  en: {
    reviewResponses: 'Review responses',
    checkNewReviews: 'Check for new reviews',
    checking: 'Checking for new reviews…',
    noReviewsYet: 'No reviews yet. Click "Check for new reviews" to pull them in.',
    draftedResponse: 'Drafted response',
    copyResponse: 'Copy response',
    copied: 'Copied ✓',
    loading: 'Loading your reviews…',
  },
  ru: {
    reviewResponses: 'Ответы на отзывы',
    checkNewReviews: 'Проверить новые отзывы',
    checking: 'Проверка новых отзывов…',
    noReviewsYet: 'Пока нет отзывов. Нажмите «Проверить новые отзывы».',
    draftedResponse: 'Черновик ответа',
    copyResponse: 'Скопировать ответ',
    copied: 'Скопировано ✓',
    loading: 'Загрузка отзывов…',
  },
  uz: {
    reviewResponses: 'Sharhlarga javoblar',
    checkNewReviews: 'Yangi sharhlarni tekshirish',
    checking: 'Yangi sharhlar tekshirilmoqda…',
    noReviewsYet: 'Hozircha sharhlar yo\'q. "Yangi sharhlarni tekshirish" tugmasini bosing.',
    draftedResponse: 'Javob loyihasi',
    copyResponse: 'Javobni nusxalash',
    copied: 'Nusxalandi ✓',
    loading: 'Sharhlar yuklanmoqda…',
  },
}
