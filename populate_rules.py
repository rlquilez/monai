import os
from database import SessionLocal
from models import Rule, RuleGroup
from datetime import datetime
from pytz import timezone

def populate_rules():
    """
    Popula o banco de dados com as regras padrão.
    """
    db = SessionLocal()
    try:
        # Lista de regras padrão
        default_rules = [
            {
                "name": "Variações Contextuais",
                "description": "Considera as variações contextuais e os padrões esperados, dando maior relevância aos dados históricos mais recentes.",
                "rule_text": "Considere as variações contextuais e os padrões esperados, dando maior relevância aos dados históricos mais recentes."
            },
            {
                "name": "Validação de Média",
                "description": "Valida se o valor de 'avg' está dentro do intervalo definido pelos valores de 'min' e 'max'.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'avg', juntamente com 'min' e 'max', o valor de 'avg' deve estar dentro do intervalo definido pelos valores de 'min' e 'max'."
            },
            {
                "name": "Validação de Média Aritmética",
                "description": "Valida se o valor de 'mean' está dentro do intervalo definido pelos valores de 'min' e 'max'.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'mean', juntamente com 'min' e 'max', o valor de 'mean' deve estar dentro do intervalo definido pelos valores de 'min' e 'max'."
            },
            {
                "name": "Validação de Máximo",
                "description": "Valida se o valor de 'max' é maior que o valor de 'min'.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'max', o valor de 'max' deve ser maior que o valor de 'min'."
            },
            {
                "name": "Validação de Desvio Padrão",
                "description": "Valida se o valor de 'std' é menor que a diferença entre os valores de 'max' e 'min'.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'std', juntamente com 'min' e 'max', o valor de 'std' deve ser menor que a diferença entre os valores de 'max' e 'min'."
            },
            {
                "name": "Validação de Desvio Padrão Alternativo",
                "description": "Valida se o valor de 'stdev' é menor que a diferença entre os valores de 'max' e 'min'.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'stdev', juntamente com 'min' e 'max', o valor de 'stdev' deve ser menor que a diferença entre os valores de 'max' e 'min'."
            },
            {
                "name": "Validação de Contagem",
                "description": "Valida se o valor de 'count' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'count', o valor de 'count' deve ser maior que zero."
            },
            {
                "name": "Validação de Soma",
                "description": "Valida se o valor de 'sum' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'sum', o valor de 'sum' deve ser maior que zero."
            },
            {
                "name": "Validação de Mediana",
                "description": "Valida se o valor de 'median' está entre os valores de 'min' e 'max'.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'median', o valor de 'median' deve estar entre os valores de 'min' e 'max'."
            },
            {
                "name": "Validação de Moda",
                "description": "Valida se o valor de 'mode' está entre os valores de 'min' e 'max'.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'mode', o valor de 'mode' deve estar entre os valores de 'min' e 'max'."
            },
            {
                "name": "Validação de Variância",
                "description": "Valida se o valor de 'variance' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'variance', o valor de 'variance' deve ser maior que zero."
            },
            {
                "name": "Validação de Assimetria",
                "description": "Valida se o valor de 'skewness' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'skewness', o valor de 'skewness' deve ser maior que zero."
            },
            {
                "name": "Validação de Curtose",
                "description": "Valida se o valor de 'kurtosis' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'kurtosis', o valor de 'kurtosis' deve ser maior que zero."
            },
            {
                "name": "Validação de Amplitude",
                "description": "Valida se o valor de 'range' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'range', o valor de 'range' deve ser maior que zero."
            },
            {
                "name": "Validação de IQR",
                "description": "Valida se o valor de 'iqr' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'iqr', o valor de 'iqr' deve ser maior que zero."
            },
            {
                "name": "Validação de MAD",
                "description": "Valida se o valor de 'mad' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'mad', o valor de 'mad' deve ser maior que zero."
            },
            {
                "name": "Validação de CV",
                "description": "Valida se o valor de 'cv' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'cv', o valor de 'cv' deve ser maior que zero."
            },
            {
                "name": "Validação de Z-Score",
                "description": "Valida se o valor de 'z_score' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'z_score', o valor de 'z_score' deve ser maior que zero."
            },
            {
                "name": "Validação de P-Valor",
                "description": "Valida se o valor de 'p_value' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'p_value', o valor de 'p_value' deve ser maior que zero."
            },
            {
                "name": "Validação de Intervalo de Confiança",
                "description": "Valida se o valor de 'confidence_interval' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'confidence_interval', o valor de 'confidence_interval' deve ser maior que zero."
            },
            {
                "name": "Validação de Limite Superior",
                "description": "Valida se o valor de 'upper_bound' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'upper_bound', o valor de 'upper_bound' deve ser maior que zero."
            },
            {
                "name": "Validação de Limite Inferior",
                "description": "Valida se o valor de 'lower_bound' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'lower_bound', o valor de 'lower_bound' deve ser maior que zero."
            },
            {
                "name": "Validação de Outliers",
                "description": "Valida se o valor de 'outliers' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'outliers', o valor de 'outliers' deve ser maior que zero."
            },
            {
                "name": "Validação de Percentis",
                "description": "Valida se o valor de 'percentiles' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'percentiles', o valor de 'percentiles' deve ser maior que zero."
            },
            {
                "name": "Validação de Decis",
                "description": "Valida se o valor de 'deciles' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'deciles', o valor de 'deciles' deve ser maior que zero."
            },
            {
                "name": "Validação de Quartis",
                "description": "Valida se o valor de 'quartiles' é maior que zero.",
                "rule_text": "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'quartiles', o valor de 'quartiles' deve ser maior que zero."
            }
        ]

        # Criar regras
        rules = []
        for rule_data in default_rules:
            rule = Rule(**rule_data)
            db.add(rule)
            rules.append(rule)
        
        db.commit()

        # Criar grupo de regras padrão
        default_group = RuleGroup(
            name="Regras Padrão",
            description="Grupo contendo todas as regras padrão do sistema.",
            is_active=True
        )
        default_group.rules = rules
        db.add(default_group)
        db.commit()

        print("Regras e grupo de regras padrão criados com sucesso!")

    except Exception as e:
        print(f"Erro ao criar regras e grupo de regras padrão: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_rules() 