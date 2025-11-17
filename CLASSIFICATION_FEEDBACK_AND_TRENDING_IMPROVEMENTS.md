# Classification Feedback and Trending News Improvements

## Summary of Changes

### 1. Training Data and API Key
**Question**: 换了 API key，但之前用了一些 excel train，即便换了 key 也沿用了之前的 train 对吗？

**Answer**: ✅ **Yes, correct!**
- Training examples (75 real examples) are **hardcoded in the prompt** in `api_classifier.py` (lines 290-356)
- These examples are included in **every API call** as part of the prompt
- Changing the API key does **NOT** affect these training data, as they are sent with each request
- The examples are not stored on OpenAI's side, but are part of the prompt you send

### 2. Classification Feedback Mechanism
**Question**: 发现还是有一些不精准，要在这个结果上告诉他吗？

**Answer**: ✅ **Added feedback mechanism!**
- Added a feedback section in the Streamlit UI (under "📰 Articles" section)
- Users can select an article and mark it as "✅ Correct" or "❌ Incorrect"
- If incorrect, users can provide the correct category
- Feedback is stored in `st.session_state.classification_feedback` for future improvements
- This feedback can be used to refine the prompt examples

### 3. Trending News Improvements
**Question**: trending news 用了 API 吗？我发现他并没有分类来统计，比如 geopolitic 有很多中日的类似报道他没有统计

**Answer**: ✅ **Fixed!**
- **Yes, trending news uses API** when `use_api_classification` is enabled
- **Problem identified**: 
  - Similarity check was done globally (across all articles), but grouping was done by category first
  - This meant cross-category similar articles (e.g., China-Japan coverage in Geopolitics and China-Russia) were not grouped together
  - `min_sources=3` threshold was too high, missing 2-source coverage

**Fixes applied**:
1. ✅ Lowered `similarity_threshold` from 0.6 to 0.55 (catches more similar articles)
2. ✅ Lowered `min_sources` from 3 to 2 (includes 2-source coverage)
3. ✅ Improved `generate_trending_rank()` to group by `GroupID` first (cross-category), then display by category
4. ✅ Added cross-category indicator in UI (shows "🌐 Cross-category coverage" when articles span multiple categories)

## Technical Details

### Trending News Flow (After Fix)
1. `group_similar_news()`: Groups all articles by similarity (across all categories) using:
   - Text similarity (fast filtering)
   - API similarity check (for ambiguous cases, when `use_api_classification=True`)
2. `generate_trending_rank()`: 
   - Groups by `GroupID` (not by category first)
   - Identifies cross-category groups
   - Displays by category but preserves cross-category information
3. UI: Shows cross-category indicator when articles span multiple categories

### API Usage in Trending News
- When `use_api_classification=True`:
  - API is called for similarity checks when text similarity is between 0.45-0.55 (ambiguous cases)
  - Uses `are_similar_articles_api()` function
  - Includes budget control and rate limiting (200ms delay)

## Next Steps
1. Collect feedback from users on misclassified articles
2. Use feedback to refine prompt examples in `api_classifier.py`
3. Monitor trending news to ensure cross-category articles are properly grouped

