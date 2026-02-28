from huey.contrib.djhuey import db_task
import logging
from .models import Article, Paragraph
from .ai_services import analyze_article_meta
from ai_analysis.services import batch_translate_texts

logger = logging.getLogger(__name__)

@db_task()
def process_article_meta_task(article_id: int):
    logger.info(f"Starting meta analysis task for Article {article_id}")
    try:
        article = Article.objects.get(id=article_id)
        
        paragraphs = list(article.paragraphs.all())
        
        # Combine title and text with paragraph IDs for context
        text_with_ids = "\n".join([f"[{p.id}] {p.content}" for p in paragraphs])
        full_text = f"TITLE: {article.title}\n{text_with_ids}"
        
        result = analyze_article_meta(title=article.title, text=full_text)
        
        # Save output dictionary to JSONField (status turns translating)
        article.meta_context = result
        article.status = 'translating'
        article.save()
        
        # Trigger paragraph translation in chunks
        chunk_size = 20
        for i in range(0, len(paragraphs), chunk_size):
            chunk = paragraphs[i:i+chunk_size]
            payload = [{"id": p.id, "text": p.content} for p in chunk]
            try:
                translations = batch_translate_texts(payload)
                trans_map = {item['id']: item.get('translation', '') for item in translations if 'id' in item}
                for p in chunk:
                    if p.id in trans_map:
                        p.translation = trans_map[p.id]
                        p.save(update_fields=['translation'])
            except Exception as e:
                logger.error(f"Error translating chunk: {e}")
        
        
        # Mark as completely ready
        article.status = 'ready'
        article.save()
        
        logger.info(f"Successfully processed Article {article_id}")
    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found.")
    except Exception as e:
        logger.exception(f"Exception during article analysis: {e}")
        try:
            article = Article.objects.get(id=article_id)
            article.status = 'failed'
            article.save()
        except:
            pass
