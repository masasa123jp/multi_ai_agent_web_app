# common/translation_service.py

import logging
import asyncio

logger = logging.getLogger(__name__)

def translate_text(text: str, target_lang: str = "en") -> str:
    """
   生成AIを利用して、与えられたテキストを指定のターゲット言語に翻訳します。
    
    Parameters:
      text: 翻訳対象のテキスト
      target_lang: 翻訳先の言語 (例: "en" なら英語)
      
    Returns:
      翻訳されたテキスト (str)
      
    ※ 翻訳APIの利用により、例えば入力が日本語の場合、英訳することで後続の生成結果の品質向上が期待できる。
    """
    if not text:
        return text

    prompt = f"Translate the following text into {target_lang}:\n{text}"
    logger.info(f"Translation prompt: {prompt}")

    try:
        # 動的インポートで循環参照を回避
        from common.ai_service import call_generative_ai
        translated_text = asyncio.run(call_generative_ai(
            model="gpt-4o",
            prompt=prompt,
            max_tokens=150
        ))
        return translated_text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text
